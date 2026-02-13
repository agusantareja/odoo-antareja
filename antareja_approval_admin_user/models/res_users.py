# -*- coding: utf-8 -*-

from odoo import models, api, tools
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_users_for_approval(self, company=None):
        if not self:
            return
        return super(ResUsers,self.filtered(lambda u: not u.admin_user)).get_users_for_approval(company=company)
