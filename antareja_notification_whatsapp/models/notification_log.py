from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)


class NotificationLog(models.Model):
    _inherit = "notification.log"

    whatsapp_id = fields.Integer()
    whatsapp_model = fields.Char()

    def action_show_whatsapp(self):
        self.ensure_one()
        if self.whatsapp_model and self.whatsapp_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.whatsapp_model,
                'view_mode': 'form',
                'res_id': self.whatsapp_id,
            }

    def send_whatsapp(self):
        result = self.notification_template_id.with_user(self.user_id).send_notification_to_user_whatsapp(
            self.receiver_id,self.res_id,
            transaction_id=self.transaction_id,
            transaction_model_name=self.transaction_model_name
        )
        if result:
            self.write(result)
