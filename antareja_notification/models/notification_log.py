from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)


class NotificationLog(models.Model):
    _name = "notification.log"
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

    def action_show_mail(self):
        self.ensure_one()
        if self.mail_model and self.mail_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.mail_model,
                'view_mode': 'form',
                'res_id': self.mail_id,
            }

    def action_show_send_message(self):
        self.ensure_one()
        if self.send_message_model and self.send_message_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.send_message_model,
                'view_mode': 'form',
                'res_id': self.send_message_id,
            }
    def action_show_chat_message(self):
        self.ensure_one()
        if self.chat_message_model and self.chat_message_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.chat_message_model,
                'view_mode': 'form',
                'res_id': self.chat_message_id,
            }
