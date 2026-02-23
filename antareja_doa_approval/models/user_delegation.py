# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class UserDelegation(models.Model):
    _name = 'user.delegation'
    _inherit = [_name, 'approval.instance.able.mixin']

    # add state for approval
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
    ])
    # request_date = fields.Date(
    #     default=fields.Date.context_today,
    # )
    approval_task_line = fields.One2many(related='approval_instance_id.approval_task_line')

    def get_internal_description(self):
        return self.note

    def get_internal_requester_id(self):
        self.ensure_one()
        return self.delegator_id.id

    def get_internal_menu_id(self):
        return "antareja_doa_approval.menu_to_approve_user_delegate"

    def create_approval_task_line(self, approval_instance=None, **kwargs):
        transaction_id = self.id
        transaction_model_name = self._name
        users = self.env['hr.employee'].get_users_approval_employee(self.delegator_id, self.company_id)
        if users:
            approval_task_line = [{"user_id": user.id, "type_approval": "user"} for user in users]
        else:
            # Default to admin user if no approver found
            approval_task_line = [{"group_id": self.env.ref('base.group_erp_manager').id, "type_approval": "group"}]
        approval_instance.clear_approval()
        if not self.env['approval.task.line'].with_context(
                default_transaction_id=transaction_id,
                default_transaction_model_name=transaction_model_name,
                default_status_approval='waiting_approval',
                default_approval_instance_id=approval_instance.id
        ).create(approval_task_line):
            raise UserError("No employee")

    def action_button_submit(self):
        return self.action_request_approval()

    def event_approval_start(self):
        self.write({'state': 'waiting_approval'})

    def event_approval_done(self, is_approved=False,is_rejected=False):
        if is_approved:
            self.sudo()._set_prepared_state()
        elif is_rejected:
            self.sudo().write({'state': 'draft'})

    def get_prepared_state(self):
        return super(UserDelegation, self).get_prepared_state() + ['approved']
