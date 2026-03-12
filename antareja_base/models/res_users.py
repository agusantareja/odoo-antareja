# -*- coding: utf-8 -*-

from odoo import models, api, tools
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

    def get_users_for_notification(self,company=None):
        if not self:
            return
        if self.env.context.get("__user_with_delegator_notification"):
            return self
        if company:
            result = self.browse()
            for user in self:
                if company.id in user.company_ids.ids:
                    result |= user
        else:
            result = self
        result = result | result.get_delegatee()
        return result.with_context(__user_with_delegator_notification=True)

    def get_users_for_approval(self,company=None):
        if not self:
            return
        if self.env.context.get("__user_with_delegator_approval"):
            return self
        if company:
            result = self.browse()
            for user in self:
                if company.id in user.company_ids.ids:
                    result |= user
            result |= self
        else:
            result = self
        result = result | result.get_delegatee()
        return result.with_context(__user_with_delegator_approval=True)

    def has_delegate_group_ext_id(self, group_ext_id):
        group = self.env.ref(group_ext_id, raise_if_not_found=False)
        return group and self.has_delegate_group_id(group.id)

    @api.model
    def has_delegate_group_id(self, group_id: int):
        """
        metode ini akan di override di modul antareja_doa
        """
        return False

    def get_delegatee(self, company_id=None):
        return self.browse()

    def get_delegators(self):
        """
        metode ini akan di override di modul antareja_doa
        """
        return self.browse()
