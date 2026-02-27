# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class NotificationLog(models.Model):
    _name = "notification.log"
    _inherit = 'approval.transaction.able.mixin'
    _description = "Notification Template"
    _order = 'id desc'

    user_id = fields.Many2one('res.users',default=lambda self: self.env.user )
    notification_template_id = fields.Many2one('notification.template')
    receiver_id = fields.Many2one('res.users')

    mail_id = fields.Integer()
    mail_model = fields.Char()

    send_message_id = fields.Integer()
    send_message_model = fields.Char()

    chat_message_id = fields.Integer()
    chat_message_model = fields.Char()

    mobile_message_id = fields.Integer()
    mobile_message_model = fields.Char()

    res_id = fields.Integer()

    def send(self):
        result = self.notification_template_id.with_user(self.user_id).send_notification_to_user(
            self.receiver_id,self.res_id,
            transaction_id=self.transaction_id,
            transaction_model_name=self.transaction_model_name
        )
        if result:
            self.write(result)

    def send_mail(self):
        result = self.notification_template_id.with_user(self.user_id).send_notification_to_user_email(
            self.receiver_id,self.res_id
        )
        if result:
            self.write({
                'mail_id':result.id,
                'mail_model':result._name,
            })

    def send_wa(self):
        result = self.notification_template_id.with_user(self.user_id).send_notification_to_user_wa(
            self.receiver_id,self.res_id
        )
        if result:
            self.write({
                'send_message_id': result.id,
                'send_message_model': result._name,
            })

    def send_chat(self):
        result = self.notification_template_id.with_user(self.user_id).send_notification_to_user_chatter(
            self.receiver_id,self.res_id
        )
        if result:
            self.write({
                'chat_message_id': result.id,
                'chat_message_model': result._name,
            })

    def send_mobile(self):
        result = self.notification_template_id.with_user(self.user_id).send_notification_to_user_mobile(
            self.receiver_id,self.res_id
        )
        if result:
            self.write({
                'mobile_message_id': result.id,
                'mobile_message_model': result._name,
            })

    def send_post_message(self):
        self.notification_template_id.with_user(self.user_id).send_comment_post(
            self.receiver_id,self.res_id,
            transaction_id=self.transaction_id,
            transaction_model_name=self.transaction_model_name
        )

    @api.model
    def _show_message(self,model,res_id):

        if model and res_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': model,
                'view_mode': 'form',
                'res_id': res_id,
            }

    def action_show_mail(self):
        self.ensure_one()
        self._show_message(self, self.mail_model and self.mail_id)

    def action_show_send_message(self):
        self.ensure_one()
        self._show_message(self, self.send_message_model and self.send_message_id)

    def action_show_chat_message(self):
        self.ensure_one()
        self._show_message(self, self.chat_message_model and self.chat_message_id)

    def action_show_mobile_message(self):
        self.ensure_one()
        self._show_message(self, self.mobile_message_model and self.mobile_message_id)
