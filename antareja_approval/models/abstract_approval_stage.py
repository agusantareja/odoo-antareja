# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.antareja_approval.tools.utils import to_integer, param_transaction_object

from odoo.exceptions import UserError


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


# ===========================
# Approval Stage Mixin
# ===========================
class AbstractApprovalStageAbleMixin(models.AbstractModel):
    _name = "approval.stage.able.mixin"
    _description = "Approval Stage Mixin"

    approval_stage_id = fields.Integer(
        'Stage ID'
    )
    approval_stage_model_name = fields.Char(
        'Stage Model Name'
    )
    approval_stage_ref = fields.Reference(
        string='Approval Stage Ref',
        selection="_selection_stage_models",
        compute='_compute_approval_stage_ref',
        inverse='_inverse_approval_stage_ref',
        store=False
    )

    @api.model
    def _selection_stage_models(self):
        """
        Mengambil model yang valid untuk dijadikan referensi.
        Bisa disaring sesuai kebutuhan (misal hanya model dengan field 'name').
        """
        models = self.env['ir.model'].search([('transient', '=', False)])
        # Filter hanya model yang punya field 'name'
        valid_models = []
        for m in models:
            try:
                valid_models.append((m.model, m.name))
            except:
                continue
        return valid_models

    @api.depends('approval_stage_model_name', 'approval_stage_id')
    def _compute_approval_stage_ref(self):
        for record in self:
            if record.approval_stage_model_name and record.approval_stage_id:
                approval_stage_id = to_integer(record.approval_stage_id)
                record.approval_stage_ref = f"{record.approval_stage_model_name},{approval_stage_id}"
            else:
                record.approval_stage_ref = False

    def _inverse_approval_stage_ref(self):
        for record in self:
            if record.approval_stage_ref:
                record.approval_stage_model_name = record.approval_stage_ref._name
                record.approval_stage_id = record.approval_stage_ref.id
            else:
                record.approval_stage_model_name = False
                record.approval_stage_id = False


# ===========================
# Next Approval Task Mixin
# ===========================
class AbstractNextApprovalTask(models.AbstractModel):
    _name = "approval.next.task.able.mixin"

    access_approval = fields.Boolean(
        string="Can Approve",
        compute="_compute_access_approval",
        search="_search_access_approval",
        store=False
    )

    next_approval_task_id = fields.Many2one(
        "approval.transaction.task",
        string="Next Approval Task"
    )
    next_approval_task_ref = fields.Many2one(related='next_approval_task_id')

    @api.depends('next_approval_task_id')
    def _compute_access_approval(self):
        """Cek apakah user login punya hak approve (langsung atau proxy) dari next_approval_task_id."""
        current_user = self.env.user
        for rec in self:
            if rec.next_approval_task_id:
                rec.access_approval = current_user in rec.next_approval_task_id.get_users()
            else:
                rec.access_approval = False

    def _search_access_approval(self, operator, value):
        """Optimized search filter untuk access_approval."""
        approval_ids = []
        current_user = self.env.user

        # Cari semua approval task yang user login termasuk get_users()
        for approval in self.next_approval_task_id.search([('status_approval', '=', APPROVAL_STATUS_NOT_APPROVE)]):
            if current_user in approval.get_users():
                approval_ids.append(approval.id)

        return [('next_approval_task_id', 'in', approval_ids)]

    def get_next_approval_task(self):
        raise NotImplementedError

    def next_task_eligible_to_approval(self):
        if self.next_approval_task_id:
            return self.next_approval_task_id.status_approval in ['draft', 'waiting', 'waiting_approval']
        return False

    def check_next_approval_task(self):
        self.ensure_one()
        next_approval_task_id =  self.get_next_approval_task()
        if not self.next_task_eligible_to_approval():
            next_approval_task_id = self.get_next_approval_task()
            if next_approval_task_id:
                self.write({'next_approval_task_id': to_integer(next_approval_task_id)})
            else:
                self.write({'next_approval_task_id': False})
        if next_approval_task_id and self.next_approval_task_id.status_approval in ['draft', 'waiting']:
            next_approval_task_id.set_waiting_approval_state()
        return next_approval_task_id


class AbstractApprovalStage(models.AbstractModel):
    _name = "abstract.approval.stage"
    _inherit = [
        'abstract.approval.status',
        'abstract.approval.strategy.config',
    ]
    _order = 'sequence , id'

    name = fields.Char('Transaction Name', required=True, help="Name of the transaction being approved.")
    description = fields.Text('Description', help="Description of the transaction being approved.")

    request_date = fields.Datetime(
        'Request Date', default=fields.Datetime.now,
        help="Date when the approval request was made.")
    requester_id = fields.Many2one(
        'res.users', 'Requester', default=lambda self: self.env.user,
        help="User who requested the approval.")

    # Transaction Details information configuration
    transaction_id = fields.Integer(
        'Transaction ID'
    )
    approval_instance_id = fields.Many2one(
        'abstract.approval.instance',
        string='Approval Instance',
        help="Reference to the approval transaction instance.",
    )
    approval_tasks = fields.One2many(
        'abstract.approval.task',
        'approval_stage_id',
        string="Approval Records",
    )
