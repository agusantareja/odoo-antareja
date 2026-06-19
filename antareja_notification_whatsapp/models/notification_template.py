# -*- coding: utf-8 -*-

import json
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class NotificationTemplate(models.Model):
    _inherit = "notification.template"

    template_whatsapp = fields.Many2one('whatsapp.template')

    def send_notification_to_user_wa(self, notification_to_user, res_id, **kwargs):
        if not notification_to_user or not res_id:
            return
        self.ensure_one()
        def get_phone_number():
            employees = self.env['hr.employee'].sudo().search([('user_id', '=', notification_to_user.id)])
            for emp in employees:
                if emp.mobile_phone:
                    return emp.mobile_phone
            return False

        if self.template_wa and kwargs.get('send_notification_whatsapp', True):
            WhatsAppTemplate = self.env['whatsapp.template']
            partner = notification_to_user.partner_id
            phone_number = partner.mobile or partner.phone or get_phone_number()
            phone = WhatsAppTemplate._format_phone_number(phone_number)
            test_wa = self.get_test_wa()
            if test_wa and test_wa != 'False':
                _logger.info(f"WA TO: {phone} --> {test_wa}")
                phone = WhatsAppTemplate._format_phone_number(test_wa)

            if not phone:
                _logger.warning("Invalid phone number for partner ID %s , name %s , %s", partner.id,partner.name,phone_number)
                return

            values = self.template_wa.with_context(notification_to_user=notification_to_user).generate_email(res_id)
            message_wa = values['body_html']
            ref = values['subject']
            payload = {
                'scope': self.scope or self.get_wa_scope_default(),
                'phone': phone,
                'message': message_wa,
                'ref': ref,
            }
            create_dict = {
                'res_id': res_id,
                'model': self.model,
                'recipient_partner_id': partner.id,
                'payload': json.dumps(payload),
                'status': 'pending',
            }
            return self.env['whatsapp.log'].sudo().create(create_dict)

        return None

    def create_new_wa_message(self, phone:str, message:str, ref:str, res_id:int, model:str, scope="LEGACY", partner=None):
        WhatsappTemplate = self.env['whatsapp.template']
        phone_formatted = WhatsappTemplate._format_phone_number(phone)
        if not phone_formatted:
            if partner:
                _logger.warning(
                    "Invalid phone number for partner ID %s , name %s , %s",
                    partner.id,
                    partner.name,
                    phone,
                )
            else:
                _logger.warning("Invalid phone number: %s", phone)
            return None

        payload = {
            'scope': scope,
            'phone': phone_formatted,
            'message': message,
            'ref': ref,
        }
        create_dict = {
            'res_id': res_id,
            'model': model,
            'payload': json.dumps(payload),
            'status': 'pending',
        }
        if partner:
            create_dict['recipient_partner_id'] = partner.id
        return self.env['whatsapp.log'].sudo().create(create_dict)

    def send_notification_to_user_whatsapp(self, notification_to_user, res_id, **kwargs):
        if not notification_to_user or not res_id:
            return
        if self.template_whatsapp and kwargs.get('send_notification_whatsapp', True):
            return self.template_whatsapp.with_context(notification_to_user=notification_to_user).send_whatsapp(res_id)

        return None

    def send_notification_to_user(self, notification_to_user, res_id, **kwargs):
        notif_log = super(NotificationTemplate,self).send_notification_to_user(notification_to_user, res_id, **kwargs) or {}
        result = self.send_notification_to_user_whatsapp(notification_to_user, res_id, **kwargs)
        if result:
            notif_log['whatsapp_id'] = result.ids[0]
            notif_log['whatsapp_model'] = result._name
        return notif_log
