# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.test_convert.tests.test_env import record
from odoo.exceptions import UserError
from ..tools.utils import have_method, save_call_method

# def have_method(obj, method):
#     return hasattr(obj, method) and callable(getattr(obj, method))


class ApprovalAccessMixin(models.AbstractModel):
    _name = "approval.access.mixin"
    _description = "Mixin : Approval Access Mixin"

    access_approval = fields.Boolean(
        string="Can Approve",
    )


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

    assign_responsible_rule = fields.Selection([
        ('legacy', 'Legacy'),
        ('have_one_user', 'Have One User'),
        ('pikcup', 'Responsible'),
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
            'approval_res_id': self.id
        }
        if self.responsible_user_id:
            kw['user_ids']= self.responsible_user_id
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
    (APPROVAL_STATUS_CANCELLED, 'Cancelled')
]


class AbstractApprovalStatus(models.AbstractModel):
    _name = "abstract.approval.status"

    status_approval = fields.Selection(
        APPROVAL_STATUS_LIST,
        'Status Approval',
        default='draft',
    )

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


class ApprovalTaskLineMixin(models.AbstractModel):
    _name = "approval.task.line.mixin"
    _description = "Approval Task Line Integration Mixin"

    reject_to_method = fields.Selection([
        ('legacy', "Legacy"),
        ('to_requestor', "To Requestor"),
        ('to_previous', "To Previous"),
        ('to_task_line', "To Task Line"),
    ], default='legacy', readonly=True)

    def get_reject_to_task_line(self):
        raise NotImplemented

    def get_approval_start_task(self,start_task):
        """
        Get list approval from start_task to this object
        """
        end_task = self.ensure_one()
        approve_task_line_between = self.browse()
        approval_task_line = self.get_all_approval_task_line()
        found_start = not start_task
        for task in approval_task_line:
            if found_start:
                if end_task.id == task.id:
                    break
                approve_task_line_between |= task
            elif task.id == start_task.id:
                found_start = True

        return approve_task_line_between

    def get_approval_instance(self):
        raise NotImplemented

    def get_all_approval_task_line(self,transaction_id=None, transaction_model_name=None):
        if self:
            transaction_id= self.transaction_id
            transaction_model_name = self.transaction_model_name
        if not transaction_model_name  or not transaction_id:
            raise UserError(" Transaction not set ")
        return self.search([('transaction_id','=',transaction_id),('transaction_model_name','=',transaction_model_name)])

    def get_previous_approval_task_line(self, transaction_id=None, transaction_model_name=None):
        end_task = self.ensure_one()
        previous = self.browse()
        approval_task_line = self.get_all_approval_task_line()
        for task in approval_task_line:
            if end_task.id == task.id:
                break
            previous = task
        return previous

    def get_next_approval_task_line(self,transaction_id=None, transaction_model_name=None):
        raise NotImplemented

    def register_approval_task(self, **kwargs):

        return self.register_to_approval_task(**kwargs)

    def register_to_approval_task(self, **kwargs):
        self.ensure_one()
        if have_method(self, "prepare_approval_task_dict"):
            kw=self.prepare_approval_task_dict()
            kw.update(kwargs)
        else:
            kw = dict(kwargs)

        transaction_object = kw.get('transaction_object') or save_call_method(self,'get_transaction_object')
        if transaction_object:
            if not self.env.context.get('skip_from_register_approval_task') and have_method(transaction_object,"register_to_approval_task"):
                return transaction_object.with_context(skip_from_register_approval_task=True).register_approval_task(**kw)
            transaction_id = transaction_object.id
            transaction_model_name = transaction_object._name
        else:
            transaction_id = kw.get('transaction_id')
            transaction_model_name = kw.get('transaction_model_name')

        return self.env['approval.task'].approval_setup(transaction_id, transaction_model_name, **kw)

    def _create_approval_audit_log(self, **kwargs):
        self.ensure_one()
        transaction_object = kwargs.get('transaction_object')
        kw = dict(kwargs)
        if transaction_object:
            if have_method(transaction_object, "create_approval_log"):
                return transaction_object.create_approval_log(**kw)
            kw.update(
                transaction_id=transaction_object.id,
                transaction_model_name=transaction_object._name
            )
        return self.env['approval.audit.log'].create_audit_log(**kw)

    def create_approval_audit_log_approved(self, **kwargs):
        kw = dict(kwargs)
        kw['action_type'] = 'approve'
        return self._create_approval_audit_log(**kw)

    def create_approval_audit_log_rejected(self, **kwargs):
        kw = dict(kwargs)
        kw['action_type'] = 'reject'
        return self._create_approval_audit_log(**kwargs)

    def send_approval_notification(self, **kwargs):
        pass

    def send_rejected_notification(self, **kwargs):
        pass

    def send_approved_notification(self, **kwargs):
        pass

    def action_approve(self):
        self.approve()

    def action_reject(self):
        self.reject(reason="No Reason")

    def set_approved_status(self, **kwargs):
        raise NotImplemented

    def approve(self, **kwargs):
        rec = self
        kw = dict(kwargs)
        kw['approval_task_line'] = rec
        rec.before_approve(**kwargs)
        rec.set_approved_status(**kwargs)
        self.after_approve(**kwargs)

    def before_approve(self, **kwargs):
        rec = self
        kw = dict(kwargs)
        kw['approval_task_line'] = rec
        approval_instance = kwargs.get('approval_instance') or rec.get_approval_instance()
        approval_instance and approval_instance.before_approve(**kw)

    def after_approve(self, **kwargs):
        rec = self
        kw = dict(kwargs)
        approval_task_line_next = rec.get_next_approval_task_line()
        kw['approval_task_line'] = rec
        kw['approval_task_line_next'] =  approval_task_line_next
        kw['is_approval_done'] = not approval_task_line_next
        approval_instance = kwargs.get('approval_instance') or rec.get_approval_instance()
        approval_instance and approval_instance.after_approve(**kw)

    def set_rejected_status(self, **kwargs):
        raise NotImplemented

    def set_waiting_status(self, **kwargs):
        raise NotImplemented

    def reject(self, reason=None, **kwargs):
        kw = dict(kwargs)
        kw['reason'] = reason
        self.before_reject(**kwargs)
        is_approval_done = False
        approve_task_line_next = None
        approve_task_line_between = self.browse()
        if self.reject_to_method == 'to_task_line':
            approve_task_line_next = self.get_reject_to_task_line()
            approve_task_line_between = self.get_approval_start_task(approve_task_line_next)
        elif self.reject_to_method == 'to_requestor':
            is_approval_done = True
            approve_task_line_between = self.get_approval_start_task(None)
        elif self.reject_to_method == 'to_previous':
            approve_task_line_next = self.get_previous_approval_task_line()
        else:
            approve_task_line_next = kwargs.get('approve_task_line_next')
            approve_task_line_between =  kwargs.get('approve_task_line_between')
        kwargs.get('is_approval_done')
        if is_approval_done:
            kw['is_approval_done'] = True
        else:
            kw['approve_task_line_next'] = approve_task_line_next
        kw['approve_task_task_between'] = approve_task_line_between
        kw['approve_task_line'] = kw['approve_task_line_reject'] = self
        self.set_rejected_status(**kw)
        self.after_reject(**kw)
        if not is_approval_done and approve_task_line_next:
            approve_task_line_next.set_waiting_status(**kw)
            if approve_task_line_between:
                approve_task_line_between.set_waiting_status(**kw)

    def before_reject(self, **kwargs):
        rec = self
        kw = dict(kwargs)
        kw['approval_task_line'] = rec
        approval_instance = kwargs.get('approval_instance') or rec.get_approval_instance()
        approval_instance and approval_instance.before_reject(**kw)

    def after_reject(self, **kwargs):
        rec = self
        kw = dict(kwargs)
        kw['approval_task_line'] = rec
        approval_instance = kwargs.get('approval_instance') or rec.get_approval_instance()
        approval_instance and approval_instance.after_reject(**kw)
