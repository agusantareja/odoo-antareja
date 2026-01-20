# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class ResGroups(models.Model):
    _inherit = 'res.groups'

    def get_users_for_notification(self, company=None):
        if self:
            return self.users.get_users_for_notification(company=company)
        return self.users.browse()

    def get_users_for_approval(self, company=None):
        if self:
            return self.users.get_users_for_approval(company=company)
        return self.users.browse()
