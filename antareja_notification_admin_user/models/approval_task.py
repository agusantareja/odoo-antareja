# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ApprovalTask(models.Model):
    _inherit = 'approval.task'

    def get_users_for_notification(self):
        users = super(ApprovalTask, self).get_users_for_notification()
        return users and users.fillerd(lambda u: not u.admin_user)
