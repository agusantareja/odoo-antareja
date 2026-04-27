# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def doa_exclude_group_ext_id(self):
        return ['base.group_user', 'base.group_system', 'base.group_erp_manager',
                           'antareja_doa.group_doa_internal_user_create']

    @tools.ormcache()
    def doa_exclude_groups(self):
        res_groups = self.env['res.groups'].browse()
        for group_name in self.doa_exclude_group_ext_id():
            res_groups |= self.env.ref(group_name)
        return res_groups
