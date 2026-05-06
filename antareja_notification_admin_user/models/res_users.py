# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_users_for_notification(self, company=None):
        if not self:
            return self
        return super(ResUsers,self.filtered(lambda u: not u.admin_user and u.id not in [1,2])).get_users_for_notification(company=company)
