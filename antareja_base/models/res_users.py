# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    @tools.ormcache('self._uid', 'group_id')
    def _has_group_id(self, group_id):
        """Checks whether user belongs to given group.
        """
        self._cr.execute("""SELECT 1 FROM res_groups_users_rel as gu
                                INNER JOIN ir_model_data d on gu.gid = d.res_id
                                WHERE uid=%s AND res_id = %s""",
                         (self._uid, group_id))
        return bool(self._cr.fetchone())

    def has_group_id(self, group_id):
        uid = self.id
        if uid and uid != self._uid:
            self = self.with_user(uid)

        return self._has_group_id(group_id)

    def get_users_for_notification(self):
        return self
