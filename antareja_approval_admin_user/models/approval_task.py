# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ApprovalTask(models.Model):
    _inherit = 'approval.task'

    def get_users_for_approval(self, **kwargs):
        users = super(ApprovalTask, self).get_users_for_approval(**kwargs)
        if users and isinstance(users, models.BaseModel):
            return users.filtered(lambda u: not u.admin_user)
        return users

    def get_users_for_mobile_approval(self, **kwargs):
        users = super(ApprovalTask, self).get_users_for_mobile_approval(**kwargs)
        if users and isinstance(users, models.BaseModel):
            return users.filtered(lambda u: not u.admin_user)
        return users
