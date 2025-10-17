# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.antareja_approval.tools.utils import to_integer
from odoo.addons.antareja_approval.tools.utils import ignore_delegated_user_context


class ApprovalAccessMixin(models.AbstractModel):
    _name = "approval.access.mixin"
    _description = "Mixin : Approval Access Mixin"

    access_approval = fields.Boolean(
        string="Can Approve",
    )


class AbstractApprovalType(models.AbstractModel):
    _name = "abstract.approval.type"
    _description = "Mixin : Approval Access Aproval"
    # Tipe approval, apakah user atau group
    type_approval = fields.Selection([
        ('user', 'User'),
        ('group', 'Group'),
        ('multi_user', 'Multi User'),
        ('multi_group', 'Multi Group'),
    ], 'Type Approval', default='user')
    user_id = fields.Many2one('res.users', 'Approval By User')
    group_id = fields.Many2one('res.groups', 'Approval By Group')
    user_ids = fields.Many2many('res.users', string='Approval By Users')
    group_ids = fields.Many2many('res.groups', string='Approval By Groups')
    def get_users(self):
        """Return daftar user unik sesuai type_approval"""
        self.ensure_one()
        users = self.env['res.users']

        if self.type_approval == 'user' and hasattr(self, 'user_id') and self.user_id:
            users = self.user_id

        elif self.type_approval == 'group' and hasattr(self, 'group_id') and self.group_id:
            users = self.group_id.users

        elif self.type_approval == 'multi_user' and hasattr(self, 'user_ids') and self.user_ids:
            users = self.user_ids

        elif self.type_approval == 'multi_group' and hasattr(self, 'group_ids') and self.group_ids:
            users = self.group_ids.mapped('users')
        else:
            # === OPSI FALLBACK ===
            if hasattr(self, 'user_id') and self.user_id:
                users |= self.user_id
            if hasattr(self, 'user_ids') and self.user_ids:
                users |= self.user_ids
            if hasattr(self, 'group_id') and self.group_id:
                users |= self.group_id.users
            if hasattr(self, 'group_ids') and self.group_ids:
                users |= self.group_ids.mapped('users')

        return users


class AbstractApprovalAccess(models.AbstractModel):
    _name = "abstract.approval.access"
    _inherit = "abstract.approval.type"
    _description = "Mixin : Approval Access Approval"

    access_approval = fields.Boolean(
        string="Can Approve",
        compute="_compute_access_rights",
        search='search_filter_access_approval',
        store=False
    )

    def _compute_access_rights(self):
        """Hitung apakah user login punya akses approve/reject."""
        current_user = self.env.user
        for rec in self:
            rec.access_approval = current_user in rec.get_users()

    def get_approval_domain(self):
        current_uid = self.env.user.id
        model_name = self._name
        table = self._table
        cr = self._cr

        ids = set()

        # CASE 1: Single User
        if 'user_id' in self._fields:
            cr.execute(f"""
                SELECT id FROM {table}
                WHERE user_id = %s
            """, (current_uid,))
            ids.update(r[0] for r in cr.fetchall())

        # CASE 2: Multi User (M2M)
        if 'user_ids' in self._fields:
            rel_table = self._fields['user_ids'].relation_table
            col_this = self._fields['user_ids'].column1
            col_user = self._fields['user_ids'].column2
            cr.execute(f"""
                SELECT {col_this} FROM {rel_table}
                WHERE {col_user} = %s
            """, (current_uid,))
            ids.update(r[0] for r in cr.fetchall())

        # CASE 3: Single Group
        if 'group_id' in self._fields:
            cr.execute(f"""
                SELECT a.id 
                FROM {table} a
                JOIN res_groups_users_rel gu ON gu.gid = a.group_id
                WHERE gu.uid = %s
            """, (current_uid,))
            ids.update(r[0] for r in cr.fetchall())

        # CASE 4: Multi Group (M2M)
        if 'group_ids' in self._fields:
            rel_table = self._fields['group_ids'].relation_table
            col_this = self._fields['group_ids'].column1
            col_group = self._fields['group_ids'].column2
            cr.execute(f"""
                SELECT DISTINCT mg.{col_this}
                FROM {rel_table} mg
                JOIN res_groups_users_rel gu ON gu.gid = mg.{col_group}
                WHERE gu.uid = %s
            """, (current_uid,))
            ids.update(r[0] for r in cr.fetchall())

        return [('id', 'in', list(ids))]

    def search_filter_access_approval(self, operator, value):
        """Search method untuk filter access_approval di tree view."""
        return self.get_approval_domain()

    def get_domain_for_current_user(self):
        """Alias lebih jelas untuk pemanggilan di luar."""
        return self.get_approval_domain()

    def search_for_current_user(self):
        """Cari record yang bisa di-approve user login."""
        return self.search(self.get_approval_domain())

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get('current_user_only'):
            approval_domain = self.get_approval_domain()
            if domain:
                if isinstance(domain, str):
                    domain = eval(domain)
                domain.extend(approval_domain)
            else:
                domain = approval_domain
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
