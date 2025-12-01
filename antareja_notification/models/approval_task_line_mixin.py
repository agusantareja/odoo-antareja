# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

from odoo.models import BaseModel

_logger = logging.getLogger(__name__)


class ApprovalTaskLine(models.AbstractModel):
    _inherit =  "approval.task.line.mixin"

    def send_approval_notification(self, **kwargs):
        self.send_notification(**kwargs)

    def send_rejected_notification(self, **kwargs):
        self.send_notification(**kwargs)

    def send_approved_notification(self, **kwargs):
        self.send_notification(**kwargs)

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
        notification_template = kwargs.get("notification_template")
        if "notification_template_id" in kwargs:
            notification_template = self.env['notification.template'].browse(kwargs.get("notification_template_id"))

        if notification_template:
            res_id,model_name = self.get_res_id_for_notification(notification_template, **kwargs)
            if res_id :
                company = self.env.company
                users = self.get_users().get_users_for_notification(company=company)
                kw = dict(kwargs)
                kw['approval_task_line']=self
                notification_template.send_notification_to_users(users,res_id,**kw)
