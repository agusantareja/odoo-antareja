# -*- coding: utf-8 -*-

import logging
import json
import traceback

from odoo import api, fields, models
from firebase_admin import messaging



_logger = logging.getLogger(__name__)

class CeriaMobileNotification(models.Model):
    _name = "ceria.mobile.notification"
    _rec_name = 'title'
    _order = 'id desc'

    state = fields.Selection([
        ('accept', 'Accepted'),
        ('error', 'Error'),
        ('ready_to_send', 'Ready'),
        ('send_error', 'Send Error'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),

    ],default='accept')

    notification_type = fields.Selection(
        [('approval', 'Approval'),
         ('info', 'Info')],
        default='approval'
    )

    to_user_id = fields.Many2one('res.users')

    title = fields.Char()
    body = fields.Text()
    image = fields.Char(help="image urls")

    source_application = fields.Char()
    source_model = fields.Char()
    source_res_id = fields.Integer()

    mobile_approval_id = fields.Many2one("ceria.mobile.approval",readonly=1)

    accept_data = fields.Text()
    errors_message = fields.Char()
    last_error = fields.Datetime()
    payload = fields.Text()
    def create_payload(self, **kwargs):
        accept_data= json.dumps(kwargs)
        return self.create([{
            'accept_data':accept_data
        }])[0]

    # -------------------------------------------------------
    # SEND
    # -------------------------------------------------------
    def get_devices_token(self):
        if self.to_user_id:
            mobile_device_ids = self.to_user_id.ceria_mobile_device_ids.search([('user_id','=',self.to_user_id.id)],order='last_active desc')
            return [mobile_device.token_fcm for mobile_device in mobile_device_ids if mobile_device.token_fcm]
        else:
            return []

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
        payload = {
            'notification':{
                'title' : self.title or None,
                'body'  :self.body or None,
                'image' : self.image or None
            }
        }
        try:
            self.env["firebase.config"]._initialize_firebase()
            accept_data = json.loads(self.accept_data or "{}")
            data_notif = accept_data.get('data') or {}
            data_notif = self.prepare_send_data(**data_notif)
            data = {k: str(v) for k, v in data_notif.items() if v}
            payload['data'] = data

            notification = messaging.Notification(
                title=self.title or None,
                body=self.body or None,
                image=self.image or None
            )
            errors={}
            send=False
            for token in tokens:
                message = messaging.Message(data=data, notification=notification, token=token)
                try:
                    messaging.send(message)
                    send=True
                except Exception:
                    err = traceback.format_exc()
                    if self.env['ceria.mobile.device'].check_activate_token_fcm(token):
                        errors['token'] =err
                        _logger.warning(err)
            if send or not errors:
                self.write({
                    'payload': json.dumps(payload,indent=4),
                    'state': 'done',
                })
            else:
                err_msg=json.dumps(errors,indent=4)
                _logger.warning(err_msg)
                self.write({
                    'payload': json.dumps(payload,indent=4),
                    'errors_message': err_msg,
                    'state': 'send_error',
                })
            return True

        except Exception:
            stack = traceback.format_exc()
            self.write({
                'payload': json.dumps(payload,indent=4),
                'state': 'send_error',
                'errors_message': stack,
                'last_error': fields.Datetime.now(),
            })
            return False

    def cron_send(self):
        self.env['firebase.config']._initialize_firebase()
        records = self.search([('state', '=', 'ready_to_send')],limit=1000)
        for rec in records:
            rec.send()

    def mark_outgoing(self):
        self.write({'state': 'ready_to_send'})

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
            notification = accept_data.get('notification') or {}
            if notification and isinstance(notification,dict):
                notification_fields = {
                    'title',
                    'body',
                    'image',
                }
                mobile_notification.update({k: v for k, v in notification.items() if k in notification_fields})
            data = accept_data.get('data') or {}
            notification_to_user = None
            if data and isinstance(data,dict):
                allowed_fields = {
                    'notification_type',
                    'source_application',
                    'source_model',
                    'source_res_id',
                }
                mobile_notification.update({k: v for k, v in data.items() if k in allowed_fields})
                notification_to_user = data.get('notification_to_user')
            if notification_to_user:
                to_user_id = self.to_user_id.search(['|',('partner_id.email','=',notification_to_user),('login','=',notification_to_user)],limit=1)
            else:
                raise ValueError("notification_to_user not found")

            if to_user_id:
                mobile_notification['to_user_id']=to_user_id.id
            else:
                raise ValueError("User not found")
            self.write({**mobile_notification, 'state': 'ready_to_send'})
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
    def prepare_send_data(self,**data):
        data_notif = dict(data)
        data_notif['notification_type'] = str(self.notification_type)
        data_notif['source_application'] = str(self.source_application)
        if self.mobile_approval_id:
            data_notif['mobile_approval_id'] = self.mobile_approval_id.id or ""
        return data_notif


    def event_update_approval(self,data=None):
        rec = self.ensure_one()
        if rec.notification_type == 'approval' and rec.to_user_id:
            if not data:
                accept_data = json.loads(self.accept_data or "{}")
                data = accept_data.get('data') or {}

            prepare_data = dict(data)

            prepare_data['user_id'] = self.to_user_id.id
            prepare_data['source_application'] = self.source_application
            prepare_data['source_model'] = self.source_model
            prepare_data['source_res_id'] = self.source_res_id

            rec.mobile_approval_id=self.env["ceria.mobile.approval"].create_approval_user(**prepare_data)
