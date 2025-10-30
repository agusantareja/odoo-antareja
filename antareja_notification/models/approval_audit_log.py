
from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))

class ApprovalAuditLog(models.Model):
    _inherit = 'approval.audit.log'

    notification_template_id = fields.Many2one("notification.template")
    notification_res_id = fields.Integer()

    def notification_requestor(self,**kwargs):
        rec = self.ensure_one()
        notification_res_id = rec.notification_res_id or kwargs.get('notification_res_id')
        if rec.notification_template_id and notification_res_id and rec.requestor_id:
            rec.notification_template_id.send_notification_to_users(rec.requestor_id,notification_res_id)
