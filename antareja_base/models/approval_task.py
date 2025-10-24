# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

from odoo.models import BaseModel

_logger = logging.getLogger(__name__)


class ApprovalTransactionTask(models.AbstractModel):
    _name = "approval.transaction.task.able.mixin"

    def done_approval_transaction_task(self, **kwargs):
        """
        Approval task as done
        """
        self.ensure_one()
        approval = self.get_approval_transaction_task()
        if approval:
            approval.approval_done(**kwargs)

        if kwargs.get("skip_create_approval_log"):
            return
        self.create_approval_log(**kwargs)

    def setup_approval_transaction_task(self, **kwargs):
        """
        Register to approval task system
        """
        self.ensure_one()
        transaction_id = self.id
        transaction_model_name = self._name
        kw = dict(kwargs)

        if 'name' not in kw:
            kw['name'] = self.display_name

        self.env['approval.task'].approval_setup(
            transaction_id, transaction_model_name, **kw
        )

    def get_approval_transaction_task(self):
        return  self.env['approval.task'].search([
            ('transaction_id','=',self.id),
            ('transaction_model_name','=',self._name),
        ],limit=1)

    def send_notification_approval(self, **kwargs):
        approval = self.get_approval_transaction_task()
        if approval:
            approval.send_notification(**kwargs)

    def create_approval_log(self, **kwargs):
        self.ensure_one()
        create_d = dict(kwargs)
        create_d['transaction_id'] = self.id
        create_d['transaction_model_name'] = self._name
        self.env['approval.audit.log'].create_audit_log(**create_d)

class ApprovalTask(models.Model):
    _name = 'approval.task'
    _inherit = 'approval.transaction.able.mixin'
    _description = 'This is Approval Task for Approval helper waiting approval'
    _order = 'create_date desc'
    name = fields.Char('Name')
    description = fields.Char()
    date = fields.Datetime(string='Create Time', readonly=True, default=fields.Datetime.now)

    transaction_id = fields.Integer(
        'Transaction ID'
    )
    transaction_model_name = fields.Char(
        'Transaction Model Name',
    )
    user_ids = fields.Many2many(
        'res.users',  'approval_task_users_rel','approval_task_id','user_id',
    )
    group_ids = fields.Many2many(
        'res.groups',  'approval_task_groups_rel','approval_task_id','group_id',
        help="Groups of users who can approve this task"
    )

    user_have_access_to_approval = fields.Boolean(
        string="Can Approve",
        compute='_compute_user_have_access_to_approval',
        search='search_filter_user_have_access_to_approval',
    )

    def _compute_user_have_access_to_approval(self):
        """Hitung apakah user login punya akses approve/reject."""
        current_user = self.env.user
        for rec in self:
            rec.user_have_access_to_approval = current_user.id in rec.get_users().ids

    def search_filter_user_have_access_to_approval(self, operator, value):
        current_uid = self.env.user.id
        cr = self._cr
        ids = set()

        # CASE: Multi User (M2M)
        if 'user_ids' in self._fields:
            rel_table = self._fields['user_ids'].relation
            col_this = self._fields['user_ids'].column1
            col_user = self._fields['user_ids'].column2
            cr.execute(f"""
                   SELECT {col_this} FROM {rel_table}
                   WHERE {col_user} = %s
               """, (current_uid,))
            ids.update(r[0] for r in cr.fetchall())

        # CASE: Multi Group (M2M)
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
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', list(ids))]
        else:
            return [('id', 'not in', list(ids))]

    def get_users(self):
        """Return daftar user unik sesuai type_approval"""
        self.ensure_one()
        users = self.env['res.users'].browse()
        if  self.user_ids:
            users |= self.user_ids

        if self.group_ids:
            users |= self.group_ids.mapped('users')

        return users

    def get_transaction_object(self):
        if not self.transaction_id or not self.transaction_model_name:
            return None

        if self.transaction_id :
            return self.env[self.transaction_model_name].browse(self.transaction_id)

        return self.env[self.transaction_model_name].browse()

    def approval_done(self, **kwargs):
        self.unlink()

    def prepare_data(self,**kwargs):
        data = dict()
        def to_list_for_m2m(values):
            if isinstance(values, BaseModel):
                return values.ids
            elif isinstance(values, list):
                return values
            return []
        if 'name' in kwargs:
            data['name'] = kwargs.get('name')
        if 'description' in kwargs:
            data['description'] = kwargs.get('description')
        if 'date' in kwargs:
            data['date'] = kwargs.get('date')
        if 'user_ids' in kwargs:
            objects = kwargs.get('user_ids')
            if objects:
                data['user_ids'] = [(6, 0, to_list_for_m2m(objects))]
        else:
            data['user_ids'] = []
        if 'group_ids' in kwargs:
            objects = kwargs.get('group_ids')
            if objects:
                data['group_ids'] = [(6, 0, to_list_for_m2m(objects))]
        else:
            data['group_ids'] = []
        return data

    def prepare_create(self,**kwargs):
        return self.prepare_data(**kwargs)

    def prepare_write(self,**kwargs):
        return self.prepare_data(**kwargs)

    def approval_setup(self, transaction_id,transaction_model_name,**kwargs):
        approval_task = self.search([
            ('transaction_id','=',transaction_id),
            ('transaction_model_name','=',transaction_model_name),
        ],limit=1)
        if approval_task:
            write_dict = self.prepare_write(**kwargs)
            approval_task.sudo().write(write_dict)
        else:
            create_dict = self.prepare_create(**kwargs)
            create_dict.update(dict(
                transaction_id=transaction_id,
                transaction_model_name=transaction_model_name,
            ))
            approval_task = self.sudo().create(create_dict)
        return approval_task

    def send_notification(self, **kwargs):
        pass
