# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.models import BaseModel
import logging

_logger = logging.getLogger(__name__)


class ApprovalTask(models.Model):
    _inherit = 'approval.task'

    notification_approval_id = fields.Many2one(
        'notification.template',
        string='Notification',
        ondelete='set null',
    )

    def prepare_data(self, **kwargs):
        data = super(ApprovalTask, self).prepare_data(**kwargs)
        notification_approval = kwargs.get("notification_approval_id")
        if notification_approval :
            data['notification_approval_id'] = notification_approval

        return data

    def get_res_id_for_notification(self,notification_approval, **kwargs):
        self.ensure_one()
        res_id = None
        model_name = None
        if notification_approval:
            model_name = notification_approval.model
            if model_name:
                if self.transaction_model_name == model_name:
                    res_id = self.transaction_id
                elif self._name == model_name:
                    res_id = self.id

        return res_id,model_name

    def send_notification(self, **kwargs):
        self.ensure_one()
        notification_approval = kwargs.get("notification_approval")
        if "notification_approval_id" in kwargs:
            notification_approval = self.env['notification.template'].browse(kwargs.get("notification_approval_id"))

        if not notification_approval:
            notification_approval = self.notification_approval_id

        if notification_approval:
            res_id,model_name = self.get_res_id_for_notification(notification_approval, **kwargs)
            if res_id :
                users = self.get_users_for_notification(**kwargs)
                notification_approval.send_notification_to_users(users,res_id)
