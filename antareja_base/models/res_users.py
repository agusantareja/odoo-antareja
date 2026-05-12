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

    def get_users_for_notification(self, company=None):
        if not self:
            return
        if self.env.context.get("__user_with_delegatee_notification"):
            return self
        if company:
            result = self.browse()
            for user in self:
                if company.id in user.company_ids.ids:
                    result |= user
        else:
            result = self
        result = result.get_notification_users(company_id=company)
        return result.with_context(__user_with_delegatee_notification=True)

    def get_users_for_approval(self, company=None):
        if not self:
            return self
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
        # Tambahkan delegatee user
        result = result | result.get_delegatee(company_id=company)
        return result.with_context(__user_with_delegatee_approval=True)

    def has_delegate_group_ext_id(self, group_ext_id):
        group = self.env.ref(group_ext_id, raise_if_not_found=False)
        return group and self.has_delegate_group_id(group.id)

    @api.model
    def has_delegate_group_id(self, group_id: int):
        """
        metode ini akan di override di modul antareja_doa
        """
        return False

    def get_notification_users(self, company_id=None):
        """
        metode ini akan di override di modul antareja_doa
        """
        return self

    def get_delegatee(self, company_id=None):
        """
        metode ini akan di override di modul antareja_doa
        """
        return self.browse()

    def get_delegators(self, company_id=None):
        """
        metode ini akan di override di modul antareja_doa
        """
        return self.browse()

    @api.model
    def get_delegate_user_group(self):
        """Get all delegations user group for this proxy user."""
        return {
            'user_ids': [],
            'group_ids': [],
            'user_delegate_ids': []
            }

    def prepare_dict_approval_task_line(self):
        if self:
            if len(self.ids) > 1:
                return {
                    'type_approval': 'multi_user',
                    'group_ids': self.ids,
                }
            else:
                return {
                    'type_approval': 'user',
                    'group_ids': self.id,
                }
        return {}