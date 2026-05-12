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

    def prepare_dict_approval_task_line(self):
        if self:
            if len(self.ids) > 1:
                return {
                    'type_approval': 'multi_group',
                    'group_ids': self.ids,
                }
            else:
                return {
                    'type_approval':'group',
                    'group_ids': self.id,
                }
        return {}