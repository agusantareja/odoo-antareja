# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ApprovalStrategyTaskMixin(models.AbstractModel):
    _inherit = "approval.strategy.task.mixin"

    def get_users_for_notify_approval_task(self):
        """Get the users for approval task."""
        users = self.get_users(include_proxy=False)
        list_users = []
        for user in users:
            list_users.extend(user.get_notification_user_ids(self.company_id.id))

        return self.env['res.users'].browse(list(set(list_users)))
