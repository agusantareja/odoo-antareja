# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ApprovalAccessMixin(models.AbstractModel):
    _inherit = "approval.access.mixin"

    access_approval = fields.Boolean(
        string="Can Approve",
    )
    access_direct_approval = fields.Boolean(
        string="Can Approve by Directly User"
    )
    access_proxy_approval = fields.Boolean(
        string="Can Approve as Proxy",
    )


class AbstractApprovalAccess(models.AbstractModel):
    _inherit = "abstract.approval.access"

    access_approval = fields.Boolean(
        string="Can Approve",
        compute="_compute_access_rights",
        search='search_filter_access_approval',
        store=False
    )

    access_direct_approval = fields.Boolean(
        string="Can Approve Directly",
        compute="_compute_access_rights",
        search='search_filter_access_approval',
        store=False
    )
    access_proxy_approval = fields.Boolean(
        string="Can Approve as Proxy",
        compute="_compute_access_rights",
        search="search_filter_access_proxy_approval",
        store=False
    )

    # =====================================
    # Fungsi utama get_users
    # =====================================
    def get_users(self, include_proxy=True):
        """Ambil list user approver untuk record ini.
        Kalau include_proxy=True, tambahkan juga proxy user yang aktif.
        """
        today = fields.Date.today()
        result_users = set()

        # 1. Ambil approver langsung
        direct_users = set()
        if self.type_approval == 'user' and getattr(self, 'user_id', False):
            direct_users.add(self.user_id.id)
        elif self.type_approval == 'group' and getattr(self, 'group_id', False):
            direct_users.update(self.group_id.users.ids)
        elif self.type_approval == 'multi_user' and getattr(self, 'user_ids', False):
            direct_users.update(self.user_ids.ids)
        elif self.type_approval == 'multi_group' and getattr(self, 'group_ids', False):
            direct_users.update(self.group_ids.mapped('users').ids)

        result_users.update(direct_users)

        # 2. Jika include_proxy, tambahkan proxy dari delegator
        if include_proxy and direct_users:
            delegations = self.env['user.delegate'].get_all_delegations_for_proxy(user_ids=list(direct_users))
            proxy_users = delegations.mapped('proxy_id.id')
            result_users.update(proxy_users)

        return self.env['res.users'].browse(result_users)

    # =====================================
    # Search helper
    # =====================================
    def search_filter_access_approval(self, operator, value):
        ids = [rec.id for rec in self if rec.access_approval]
        return [('id', 'in', ids)]

    def search_filter_access_direct_approval(self, operator, value):
        ids = [rec.id for rec in self if rec.access_direct_approval]
        return [('id', 'in', ids)]

    def search_filter_access_proxy_approval(self, operator, value):
        ids = [rec.id for rec in self if rec.access_proxy_approval]
        return [('id', 'in', ids)]

    def _compute_access_rights(self):
        current_user = self.env.user
        for rec in self:
            direct_users = rec.get_users(include_proxy=False).ids
            all_users = rec.get_users(include_proxy=True).ids

            rec.access_direct_approval = current_user.id in direct_users
            rec.access_proxy_approval = (
                    current_user.id in all_users and current_user.id not in direct_users
            )
            rec.access_approval = rec.access_direct_approval or rec.access_proxy_approval

    def get_domain_for_current_user(self):
        proxy_only = self.env.context.get('proxy_only')
        direct_only = self.env.context.get('direct_only')
        # Delegasi aktif
        domain = []
        if (not proxy_only and not direct_only) or (proxy_only and direct_only):
            domain = self.search_filter_access_approval('=', True)
        elif proxy_only:
            domain = self.search_filter_access_proxy_approval('=', True)
        elif direct_only:
            domain = self.search_filter_access_direct_approval('=', True)
        else:
            # Default case, if no context is set, return all approvals
            domain = [('id', '=', False)]
        return domain

    def search_for_current_user(self):
        domain = self.get_domain_for_current_user()
        return self.search(domain)

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        proxy_only = self.env.context.get('proxy_only')
        direct_only = self.env.context.get('direct_only')
        current_user = self.env.context.get('current_user_only') or proxy_only or direct_only
        if current_user:
            if domain:
                # If domain is provided, use it directly
                if isinstance(domain, str):
                    domain = eval(domain)
                domain.extend(self.get_domain_for_current_user())
            else:
                domain = self.get_domain_for_current_user()

        return super(AbstractApprovalAccess, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                               order=order)
