# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ApprovalTaskLine(models.AbstractModel):
    _inherit =  "approval.task.line.mixin"

    def send_approval_notification(self, **kwargs):
        approval_template = kwargs.get('approval_template')
        if not kwargs.get('notification_template') and approval_template:
            kwargs = dict(kwargs)
            kwargs['notification_template'] = approval_template.notification_approval_id
        super(ApprovalTaskLine,self).send_approval_notification(**kwargs)

    def send_rejected_notification(self, **kwargs):
        approval_template = kwargs.get('approval_template')
        if not kwargs.get('notification_template') and approval_template:
            kwargs = dict(kwargs)
            kwargs['notification_template']=approval_template.notification_rejection_id

        super(ApprovalTaskLine,self).send_rejected_notification(**kwargs)

    def send_approved_notification(self, **kwargs):
        approval_template = kwargs.get('approval_template')
        if not kwargs.get('notification_template') and approval_template:
            kwargs = dict(kwargs)
            kwargs['notification_template'] = approval_template.notification_approved_id
        super(ApprovalTaskLine,self).send_approved_notification(**kwargs)

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
            res_id, model_name = self.get_res_id_for_notification(notification_template, **kwargs)
            if res_id :
                if 'company_id' in self._fields:
                    company = self.company_id
                else:
                    company = self.env.company
                users = None
                kw = dict(kwargs)
                if 'users' in kw:
                    users = kw.pop('users')
                if not users:
                    users = self.get_users_for_notification(company=company)
                else:
                    users = users.get_users_for_notification(company=company)

                kw['approval_task_line']=self
                if 'res_id' in kw:
                    kw.pop('res_id')

                notification_template.send_notification_to_users(users, res_id, **kw)
