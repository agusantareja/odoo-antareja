# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.models import BaseModel
import logging

_logger = logging.getLogger(__name__)


class ApprovalTask(models.Model):
    _name = 'approval.task'
    _inherit = 'approval.transaction.view.able.mixin'
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
    requester_id = fields.Many2one(
        'res.users', 'Requester',
        default=lambda self: self.env.user,
        help="User who requested the approval."
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
        delegators = self.env.user.get_delegators()
        if delegators:
            user_and_delegator = delegators | self.env.user
            user_filter = f"IN ({', '.join(str(d.id) for d in user_and_delegator)})"
        else:
            user_filter = f"= {current_uid}"
        # CASE: Multi User (M2M)
        if 'user_ids' in self._fields:
            rel_table = self._fields['user_ids'].relation
            col_this = self._fields['user_ids'].column1
            col_user = self._fields['user_ids'].column2
            cr.execute(f"""
                   SELECT {col_this} FROM {rel_table}
                   WHERE {col_user} {user_filter}
               """)
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
                   WHERE gu.uid {user_filter}
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
        if self:
            records = self
        else:
            transaction_id = kwargs.get('transaction_id')
            transaction_model_name = kwargs.get('transaction_model_name')
            if transaction_id and transaction_id:
                records = self.search([('transaction_id', '=', transaction_id),('transaction_model_name', '=', transaction_model_name),])
            else:
                return True
        return records.unlink()

    def prepare_data(self,**kwargs):
        data = dict()

        def to_list_for_m2m(values):
            if isinstance(values, BaseModel):
                return values.ids
            elif isinstance(values, list):
                return values
            return []

        for key in ['name', 'description', 'date', 'view_name','requester_id']:
            value = kwargs.get(key, None)
            if value is not None:
                data[key] = value

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

    def action_approval_transaction(self):
        win_dict = super(ApprovalTask, self).action_approval_transaction()
        rec = self.ensure_one()
        if rec.view_name:
            model = self.env['ir.model'].search([('model', '=', rec.transaction_model_name)], limit=1)
            if rec.group_ids:
                query = """
                        SELECT perm_read
                        FROM ir_model_access 
                        WHERE model_id = %s
                        AND group_id IN (SELECT hid FROM res_groups_implied_rel WHERE gid = %s)
                    """ % (model.id, rec.group_ids.ids[0])
                self._cr.execute(query)
                ress = self._cr.fetchall()
            else:
                ress = None
            if ress and any([x[0] for x in ress]):
                obj_ir_view = self.env["ir.ui.view"]
                obj_ir_view_browse = obj_ir_view.search(
                    [("name", "=", rec.view_name), ("model", "=", rec.transaction_model_name)])
                win_dict['view_id'] = obj_ir_view_browse.id

        return win_dict
