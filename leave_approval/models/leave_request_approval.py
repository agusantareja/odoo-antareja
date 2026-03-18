from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.antareja_approval.models.abstract_approval_stage import APPROVAL_STATUS_NOT_APPROVE, \
    APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED, APPROVAL_STATUS_CANCELLED


class LeaveRequestApproval(models.Model):
    _name = 'leave.leave_approval'
    _inherit = [_name, 'approval.strategy.task.inline.mixin']

    def get_transaction_object(self):
        return self.lr_id

    def search_for_capture(self,transaction_object,approval_stage):
        return self.search(
            [
                ('status_approval', 'in', ['draft', 'waiting', 'waiting_approval', False]),
                ('lr_id', '=', transaction_object.id),
                ('approval_stage_id', '!=', approval_stage.id),
                # ('migrate_to_id', '=', False),
            ]
        )

    type_approval = fields.Selection(
        [('user', 'User'), ('group', 'Group')], 'Type Approval',
        default='user')
    user_id = fields.Many2one(
        'res.users', 'Approval By User',
        related='employee_id', store=True, readonly=False,
        help="User who is responsible for approving the material requisition")
    approve = fields.Boolean(compute="update_status", store=True)
    status = fields.Selection([
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled'),
    ], string='Status', compute="update_status", store=True)

    @api.depends('status_approval')
    def update_status(self):
        for rec in self:
            if APPROVAL_STATUS_APPROVED == rec.status_approval:
                rec.status = 'approved'
            else:
                if APPROVAL_STATUS_REJECTED == rec.status_approval:
                    rec.status = 'rejected'
                elif APPROVAL_STATUS_CANCELLED == rec.status_approval:
                    rec.status = 'canceled'
                else:
                    rec.status = 'waiting_approval'
