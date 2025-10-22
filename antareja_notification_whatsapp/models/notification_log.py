from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)


class NotificationLog(models.Model):
    _inherit = "notification.log"

    whatapp_id = fields.Integer()
    whatapp_model = fields.Char()

    def action_show_whatapp(self):
        self.ensure_one()
        if self.whatapp_model and self.whatapp_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': self.whatapp_model,
                'view_mode': 'form',
                'res_id': self.whatapp_id,
            }
