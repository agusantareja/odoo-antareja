# -*- coding: utf-8 -*-

from odoo import api, fields, models

from ..tools.utils import have_method


class ApprovalAccessMixin(models.AbstractModel):
    _name = "approval.access.mixin"
    _description = "Mixin : Approval Access Mixin"

    access_approval = fields.Boolean(
        string="Can Approve",
    )


class ApprovalTieredMatrixRuleMixin(models.Model):
    _name = "approval.matrix.rule.mixin"
    _description = """ """

    def get_approval_matrix_rule(self, **kwargs):
        raise NotImplementedError(
            "Method get_approval_matrix_rule harus diimplementasikan di model yang mewarisi ApprovalMatrixRuleMixin"
        )

    def get_approval_line(self, **kwargs):
        raise NotImplementedError(
            "Method get_approval_line harus diimplementasikan di model yang mewarisi ApprovalMatrixRuleMixin"
        )

    def prepare_list_approval_task_line(self, **kwargs):
        raise NotImplementedError(
            "Method get_approval_matrix_rule harus diimplementasikan di model yang mewarisi ApprovalMatrixRuleMixin"
        )


class ApprovalTaskLineAssignmentMixin(models.AbstractModel):
    _name = "approval.task.line.assignment.mixin"
    _description = "Mixin : Approval Task Line Assignment"

    responsible_user_id = fields.Many2one('res.users', 'Responsible User')

    def search_responsible_user(self, user_id):
        return self.search([('responsible_user_id', '=', user_id)])

    def revoke_assignment(self):
        self.write({
            'responsible_user_id': False,
        })

    def do_assignment(self, new_user_id, reason=None):
        if have_method(self, 'get_users'):
            old_users = self.get_users()
        else:
            old_users = self.responsible_user_id
        self.env['approval.task.assignment.history'].sudo().create([{
            'task_line_id': self.id,
            'task_line_model': self._name,
            'from_user_ids': [(6, 0, old_users.ids)] if old_users else [],
            'new_user_id': int(new_user_id),
            'reason': reason,
            'reassigned_by': self.env.uid
        }])
        self.write({
            'responsible_user_id': int(new_user_id),
        })
        if have_method(self, "register_to_approval_task"):
            self.register_to_approval_task()

    def action_assignment(self):
        self.ensure_one()
        if have_method(self, 'get_users'):
            old_users = self.get_users()
        else:
            old_users = self.responsible_user_id
        # call wizard to select new user and reason
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reassign Approval Task',
            'res_model': 'approval.task.line.assignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_line_id': self.id,
                'default_task_line_model': self._name,
                'default_from_user_ids': old_users.ids if old_users else [],
            }
        }


class ApprovalTaskLineAccess(models.AbstractModel):
    _name = "approval.task.line.access.mixin"

    access_approval = fields.Boolean(
        string="Can Approve",
        compute="_compute_access_rights",
        store=False,
    )

    @api.depends_context('uid')
    def _compute_access_rights(self):
        """Hitung apakah user login punya akses approve/reject."""
        current_user = self.env.user
        for rec in self:
            rec.access_approval = current_user in rec.get_users_for_approval()

    def get_users(self):
        return self.env['res.users'].browse()

    def get_groups(self):
        return self.env['res.groups'].browse()

    def prepare_approval_task_dict(self):
        """Prepare dict untuk create record approval task."""
        self.ensure_one()
        kw = {
            'approval_task_line': self,
            'approval_model': self._name,
            'approval_res_id': self.id,
        }
        return kw

    def get_users_for_approval(self, **kwargs):
        record = self.ensure_one()
        users = kwargs.get('users') or record.get_users()
        company = None
        if 'company_id' in self._fields:
            company = self.company_id
        return users.get_users_for_approval(company=company)

    def get_users_for_notification(self, **kwargs):
        record = self.ensure_one()
        users = kwargs.get('users') or record.get_users()
        company = None
        if 'company_id' in self._fields:
            company = self.company_id
        return users.get_users_for_notification(company=company)


class AbstractApprovalType(models.AbstractModel):
    _name = "abstract.approval.type"
    _description = "Mixin : Approval Access Type"
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
    company_id = fields.Many2one('res.company', 'Company')
    assign_responsible_rule = fields.Selection([
        ('legacy', 'Legacy'),
        ('have_one_user', 'Have One User'),
        ('pickup', 'Pickup Responsible'),
    ], 'Responsible', default='legacy')

    responsible_user_id = fields.Many2one('res.users', 'Responsible User')

    def get_users(self):
        """Return daftar user unik sesuai type_approval"""
        self.ensure_one()
        if self.responsible_user_id:
            return self.responsible_user_id
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

    def get_groups(self):
        self.ensure_one()
        groups = self.env['res.groups']

        if self.type_approval == 'group' and hasattr(self, 'group_id') and self.group_id:
            groups = self.group_id
        elif self.type_approval == 'multi_group' and hasattr(self, 'group_ids') and self.group_ids:
            groups = self.group_ids
        else:
            # === OPSI FALLBACK ===
            if hasattr(self, 'group_id') and self.group_id:
                groups |= self.group_id
            if hasattr(self, 'group_ids') and self.group_ids:
                groups |= self.group_ids

        return groups

    def prepare_approval_task_dict(self):
        """Prepare dict untuk create record approval task"""
        self.ensure_one()

        kw = {
            'approval_task_line': self,
            'approval_model': self._name,
            'approval_res_id': self.id,
        }
        if self.responsible_user_id:
            kw['user_ids'] = self.responsible_user_id
            return kw

        users = self.env['res.users'].browse()
        groups = self.env['res.groups'].browse()
        if self.type_approval == 'user' and self.user_id:
            users |= self.user_id

        elif self.type_approval == 'group' and self.group_id:
            groups |= self.group_id

        elif self.type_approval == 'multi_user' and self.user_ids:
            users = self.user_ids
        elif self.type_approval == 'multi_group' and self.group_ids:
            groups = self.group_ids
        else:
            # === OPSI FALLBACK ===
            if self.user_id:
                users |= self.user_id
            if self.user_ids:
                users |= self.user_ids
            if self.group_id:
                groups |= self.group_id
            if self.group_ids:
                groups |= self.group_ids
        if users:
            kw['user_ids'] = users
        if groups:
            kw['group_ids'] = groups

        return kw

    def get_users_for_approval(self, **kwargs):
        record = self.ensure_one()
        users = kwargs.get('users') or record.get_users()
        company = None
        if 'company_id' in self._fields:
            company = self.company_id
        return users.get_users_for_approval(company=company)

    def get_users_for_notification(self, **kwargs):
        record = self.ensure_one()
        users = kwargs.get('users') or record.get_users()
        company = None
        if 'company_id' in self._fields:
            company = self.company_id
        return users.get_users_for_notification(company=company)


class AbstractApprovalAccess(models.AbstractModel):
    _name = "abstract.approval.access"
    _inherit = "abstract.approval.type"
    _description = "Mixin : Approval Access Approval"

    access_approval = fields.Boolean(
        string="Can Approve",
        compute="_compute_access_rights",
        search='search_filter_access_approval',
        store=False,
    )

    def _compute_access_rights(self):
        """Hitung apakah user login punya akses approve/reject."""
        current_user = self.env.user
        for rec in self:
            rec.access_approval = current_user in rec.get_users_for_approval()

    def get_approval_domain(self):
        current_uid = self.env.user.id
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
            rel_table = self._fields['user_ids'].relation
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
            rel_table = self._fields['group_ids'].relation
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
        return self.search(self.get_domain_for_current_user())

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get('current_user_only'):
            approval_domain = self.get_domain_for_current_user()
            if domain:
                if isinstance(domain, str):
                    domain = eval(domain)
                domain.extend(approval_domain)
            else:
                domain = approval_domain
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)


APPROVAL_STATUS_READY = 'ready'
APPROVAL_STATUS_NOT_APPROVE = 'waiting_approval'
APPROVAL_STATUS_APPROVED = 'approved'
APPROVAL_STATUS_REJECTED = 'rejected'
APPROVAL_STATUS_CANCELLED = 'cancelled'
APPROVAL_STATUS_LIST = [
    ('draft', 'Draft'),
    ('waiting', 'Waiting'),
    (APPROVAL_STATUS_NOT_APPROVE, 'Waiting Approval'),
    (APPROVAL_STATUS_APPROVED, 'Approved'),
    (APPROVAL_STATUS_REJECTED, 'Rejected'),
    (APPROVAL_STATUS_CANCELLED, 'Cancelled'),
]


class AbstractApprovalStatus(models.AbstractModel):
    _name = "abstract.approval.status"

    status_approval = fields.Selection(
        APPROVAL_STATUS_LIST,
        'Status Approval',
        default='draft',
    )

    @api.model
    def domain_waiting_status(self):
        return [('status_approval', 'in', [APPROVAL_STATUS_NOT_APPROVE, 'waiting', 'draft'])]

    def set_waiting_state(self):
        self.status_approval = 'waiting'

    def set_waiting_approval_state(self):
        self.status_approval = APPROVAL_STATUS_NOT_APPROVE

    def set_approve_state(self):
        self.status_approval = APPROVAL_STATUS_APPROVED

    def set_reject_state(self):
        self.status_approval = APPROVAL_STATUS_REJECTED

    def set_canceled_state(self):
        self.status_approval = APPROVAL_STATUS_CANCELLED
