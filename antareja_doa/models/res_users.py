# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    proxy_ids = fields.One2many(
        'user.delegate',
        'proxy_id',
        string='Proxy for Users',
        help="List of users delegated to this user."
    )

    proxy_user_ids = fields.Many2many(
        'res.users',
        string='Delegator Users',
        compute='_compute_proxy_user_group_ids',
        store=False,
        readonly=True,
        help="Users who delegated to this user."
    )

    proxy_group_ids = fields.Many2many(
        'res.groups',
        string='Delegator Groups',
        compute='_compute_proxy_user_group_ids',
        store=False,
        readonly=True,
        help="Groups from users who delegated to this user."
    )

    @api.depends('proxy_ids.delegator_id.groups_id')
    def _compute_proxy_user_group_ids(self):
        for user in self:
            # Ambil semua delegator dari proxy_ids
            delegators = user.proxy_ids.mapped('delegator_id')
            user.proxy_user_ids = delegators

            # Gabungkan semua group dari delegators
            group_set = self.env['res.groups'].browse()
            for delegator in delegators:
                group_set |= delegator.groups_id
            user.proxy_group_ids = group_set

    delegate_ids = fields.One2many(
        'user.delegate',
        'delegator_id',
        string='Delegated to Users',
        help="List of users delegated by this user."
    )

    def has_group(self, group_ext_id=None):
        # use singleton's id if called on a non-empty recordset, otherwise
        # context uid
        # addons documents call document
        if not group_ext_id:
            # perlu di chek lebih lanjut dugaan kuat bahwa js dari addons tidak mengirimkan infomasi yang benar
            _logger.warning(
                "User %s has group call without group_ext_id",
                self
            )
            return False

        base_groups_access = super(ResUsers, self).has_group(group_ext_id)
        # Always return True for base.group_user
        if base_groups_access or group_ext_id is None or group_ext_id in ['base.group_user', 'base.group_system',
                                                                          'base.group_erp_manager',
                                                                          'base.user_root', 'base.user_admin']:
            return base_groups_access

        base_groups_access = self.has_delegate_group_ext_id(group_ext_id)
        if base_groups_access:
            _logger.info(
                "User %s has group %s through delegation.",
                self.login, group_ext_id
            )
        return base_groups_access

    def has_group_id(self, group_id, with_delegate=True):
        return super(ResUsers, self).has_group_id(group_id) or (with_delegate and self.has_delegate_group_id(group_id))

    def has_delegate_group_id(self, group_id: int):
        """
        Checks this user as delegate/proxy user have DoA form delegator user given group delegator user to delegate/proxy user.
        """
        if group_id:
            uid = self.id
            if uid and uid != self._uid:
                self = self.with_user(uid)
            return self.env['user.delegate'].proxy_has_delegate_group(self._uid, group_id)
        else:
            return False

    def get_delegate_user_group(self):
        """
        Get all delegations user group for this proxy user.
        :return: {
            'user_ids': [user_id1, user_id2, ...],
            'group_ids': [group_id1, group_id2, ...]
            }
        """
        uid = self.id
        if uid and uid != self._uid:
            uid = self._uid
        return self.env['user.delegate'].get_delegations_user_group_for_proxy(uid)

    def get_notification_users(self, company_id=None):
        if self:
            notification_users_ids = self.env['user.delegate'].get_notification_user_ids(self.ids, company_id=company_id)
            if notification_users_ids:
                return self.browse(notification_users_ids)
        return self.browse()

    def get_delegators(self, company_id=None):
        if self:
            delegator_ids = self.env['user.delegate'].get_all_delegator(self.ids, company_id=company_id)
            if delegator_ids:
                return self.browse(delegator_ids)
        return self.browse()

    def get_delegatee(self, company_id=None):
        if self:
            delegatee_ids = self.env['user.delegate'].get_all_delegatee(self.ids, company_id=company_id)
            if delegatee_ids:
                return self.browse(delegatee_ids)
        return self.browse()
