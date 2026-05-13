# -*- coding: utf-8 -*-

import json
import logging
import traceback

from firebase_admin import messaging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CeriaMobileNotification(models.Model):
    _name = "ceria.mobile.notification"
    _rec_name = 'title'
    _order = 'id desc'

    state = fields.Selection([
        ('accept', 'Accepted'),
        ('error', 'Error'),
        ('ready', 'Ready'),
        ('send_error', 'Send Error'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='accept')

    notification_type = fields.Selection([
        ('approval', 'Approval'),
        ('info', 'Info'),
    ], default='approval')

    to_user_id = fields.Many2one('res.users')

    title = fields.Char()
    body = fields.Text()
    image = fields.Char(help="image urls")

    source_application = fields.Char()
    source_model = fields.Char()
    source_res_id = fields.Integer()

    accept_data = fields.Text()
    errors_message = fields.Char()
    last_error = fields.Datetime()
    payload = fields.Text()

    def create_payload(self, **kwargs):
        accept_data = json.dumps(kwargs)
        return self.create([{'accept_data': accept_data}])

    # -------------------------------------------------------
    # SEND
    # -------------------------------------------------------
    def get_devices_token(self):
        if not self.to_user_id:
            return []
        mobile_devices = self.to_user_id.ceria_mobile_device_ids.sorted(key='last_active', reverse=True)
        return [device.token_fcm for device in mobile_devices if device.token_fcm]

    def send(self):
        self.ensure_one()
        tokens = self.get_devices_token()
        if not tokens:
            self.write({
                'state': 'send_error',
                'errors_message': 'Missing FCM device token.',
                'last_error': fields.Datetime.now(),
            })
            return False
        title = self.title or None
        body = self.body or None
        image = self.image or None
        payload = {
            'notification': {
                'title': title,
                'body': body,
                'image': image,
            },
        }
        message = None
        try:
            self.env["firebase.config"]._initialize_firebase()
            accept_data = json.loads(self.accept_data or "{}")
            data_notif = accept_data.get('data') or {}
            data_notif = self.prepare_send_data(**data_notif)
            data = {k: str(v) for k, v in data_notif.items() if v}
            payload['data'] = data
            notification = messaging.Notification(title=title, body=body, image=image)
            android_config = messaging.AndroidConfig(
                priority='high',
                ttl=3600,
                collapse_key="update",
            )
            apns_config = messaging.APNSConfig(
                headers={
                    "apns-priority": "10",
                },
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default",
                        content_available=True,
                    ),
                ),
            )
            errors = {}
            sent = False
            for token in tokens:
                message = messaging.Message(
                    data=data,
                    notification=notification,
                    token=token,
                    android=android_config,
                    apns=apns_config,
                )
                try:
                    response = messaging.send(message)
                    _logger.info("Mobile Notif to user [%s], (%s), using token %s", self.to_user_id.name, response, token)
                    sent = True
                except Exception:
                    err = traceback.format_exc()
                    if self.env['ceria.mobile.device'].check_active_token_fcm(token):
                        errors[token] = err
                        _logger.warning(err)
                    else:
                        _logger.error(err)

            if sent or not errors:
                self.write({
                    'payload': (message and str(message)) or json.dumps(payload, indent=4),
                    'state': 'done',
                })
            else:
                err_msg = json.dumps(errors, indent=4)
                _logger.warning(err_msg)
                self.write({
                    'payload': (message and str(message)) or json.dumps(payload, indent=4),
                    'errors_message': err_msg,
                    'state': 'send_error',
                })
            return True
        except Exception:
            stack = traceback.format_exc()
            self.write({
                'payload': (message and str(message)) or json.dumps(payload, indent=4),
                'state': 'send_error',
                'errors_message': stack,
                'last_error': fields.Datetime.now(),
            })
            return False

    def cron_send(self):
        self.env['firebase.config']._initialize_firebase()
        records = self.search([('state', '=', 'ready')], limit=1000)
        for rec in records:
            rec.send()

    def mark_outgoing(self):
        self.write({'state': 'ready'})

    def cancel(self):
        self.write({'state': 'cancel'})

    # -------------------------------------------------------
    # PROCESS ACCEPT DATA
    # -------------------------------------------------------
    def process(self):
        self.ensure_one()
        try:
            accept_data = json.loads(self.accept_data or "{}")
            mobile_notification = {}
            notification_to_user = None
            to_user = self.to_user_id.browse()

            notification = accept_data.get('notification') or {}
            if notification and isinstance(notification, dict):
                notification_fields = {
                    'title',
                    'body',
                    'image',
                }
                mobile_notification.update({k: v for k, v in notification.items() if v and k in notification_fields})

            data = accept_data.get('data') or {}
            if data and isinstance(data, dict):
                allowed_fields = {
                    'notification_type',
                    'source_application',
                    'source_model',
                    'source_res_id',
                }
                mobile_notification.update({k: v for k, v in data.items() if k in allowed_fields})
                notification_to_user = data.get('notification_to_user')

            mobile_notification.setdefault("body", accept_data.get("body"))
            mobile_notification.setdefault("title", accept_data.get("title"))
            notification_to_user = accept_data.get('email') or notification_to_user
            mobile_phone = accept_data.get('phone')

            if notification_to_user:
                to_user = self.to_user_id.search(['|', ('partner_id.email', '=', notification_to_user), ('login', '=', notification_to_user)], limit=1)

            if not to_user and mobile_phone:
                phones = [mobile_phone]
                if mobile_phone.startswith("62"):
                    phones.append("0" + mobile_phone[2:])
                _logger.info("Searching for phones: %s", phones)
                employee = self.env['hr.employee'].search([('mobile_phone', 'in', phones)], limit=1)
                to_user = employee.user_id

            if not to_user:
                _logger.error("User not found for phone %s, email or user %s", mobile_phone, notification_to_user)
                raise ValueError("User not found")

            mobile_notification['to_user_id'] = to_user.id
            self.write({**mobile_notification, 'state': 'ready'})
            self.event_update_approval(data)
        except Exception:
            stack_trace = traceback.format_exc()
            self.write({
                'errors_message': stack_trace,
                'state': 'error',
                'last_error': fields.Datetime.now(),
            })

    # -------------------------------------------------------
    # SEND PAYLOAD
    # -------------------------------------------------------
    def prepare_send_data(self, **data):
        self.ensure_one()
        data_notif = dict(data)
        data_notif['notification_type'] = str(self.notification_type)
        data_notif['source_application'] = str(self.source_application)
        if self.mobile_approval_id:
            data_notif['mobile_approval_id'] = self.mobile_approval_id.id
        return data_notif

    def event_update_approval(self, data=None):
        pass
        # rec = self.ensure_one()
        # if rec.notification_type == 'approval' and rec.to_user_id:
        #     if not data:
        #         accept_data = json.loads(self.accept_data or "{}")
        #         data = accept_data.get('data') or {}
        #
        #     prepare_data = dict(data)
        #
        #     prepare_data['user_id'] = self.to_user_id.id
        #     prepare_data['source_application'] = self.source_application
        #     prepare_data['source_model'] = self.source_model
        #     prepare_data['source_res_id'] = self.source_res_id
        #
        #     rec.mobile_approval_id=self.env["ceria.mobile.approval"].create_approval_user(**prepare_data)
