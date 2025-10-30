# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from .abstract_approval_stage import APPROVAL_STATUS_NOT_APPROVE, APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED, \
    APPROVAL_STATUS_CANCELLED, APPROVAL_STATUS_LIST
from ..tools.utils import ignore_delegated_user_context


# ===========================
# Approval Task Mixin
# ===========================
class AbstractApprovalTaskMixin(models.AbstractModel):
    _name = "approval.task.able.mixin"
    _description = "Approval Task Mixin"

    approval_task_id = fields.Integer('Task ID')
    approval_task_model_name = fields.Char('Task Model Name')
    approval_task_ref = fields.Reference(
        string='Approval Task Ref',
        selection="_selection_task_models",
        compute='_compute_approval_task_ref',
        inverse='_inverse_approval_task_ref',
        store=False
    )

    @api.model
    def _selection_task_models(self):
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

    @api.depends('approval_task_model_name', 'approval_task_id')
    def _compute_approval_task_ref(self):
        for record in self:
            model = record.approval_task_model_name
            res_id = record.approval_task_id
            if model and res_id:
                record_ok = self.env[model].browse(res_id).exists()
                if record_ok:
                    record.approval_task_ref = f"{model},{res_id}"
                else:
                    record.approval_task_ref = False
            else:
                record.approval_task_ref = False

    def _inverse_approval_task_ref(self):
        for record in self:
            if record.approval_task_ref:
                record.approval_task_model_name = record.approval_task_ref._name
                record.approval_task_id = record.approval_task_ref.id
            else:
                record.approval_task_model_name = False
                record.approval_task_id = False


class ApprovalBuUserTask(models.AbstractModel):
    _name = "approval.user.task.mixin"
    _description = "Mixin : Approval Transaction"
    _order = 'sequence, id'

    user_execution_id = fields.Many2one(
        'res.users',
        'User Execution',
        help="User who executed approval (Approve/Reject)the transaction"
    )
    date_execution = fields.Datetime('Date Execution')
    reason_approval = fields.Text('Reason Approval')

    def set_user_execution_id(self):
        self.user_execution_id = self.env.user

    def _approve_task(self):
        """Approve the transaction"""
        self.ensure_one()
        self.date_execution = fields.Datetime.now()
        self.set_user_execution_id()

    def _reject_task(self):
        """Reject the transaction"""
        self.ensure_one()
        self.date_execution = fields.Datetime.now()
        self.reason_approval = self.env.context.get('__reject_reason')
        self.set_user_execution_id()


class AbstractApprovalTask(models.AbstractModel):
    _name = "abstract.approval.task"
    _inherit = ['abstract.approval.access', 'abstract.approval.status','approval.user.task.mixin']
    _description = "Mixin : Approval Transaction"
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10, help="Sequence of the approval stage in the transaction")

    approval_stage_id = fields.Many2one('abstract.approval.stage')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, string='Company'
    )

    def validate_before_approve_or_reject(self):
        if self.status_approval != APPROVAL_STATUS_NOT_APPROVE:
            raise ValidationError("Transaction is already approved or rejected.")
        if not self.access_approval :
                raise ValidationError("You are not authorized to approve this transaction.")

    def _approve_task(self):
        """Approve the transaction"""
        self.ensure_one()
        self.validate_before_approve_or_reject()
        self.set_approve_state()
        super(AbstractApprovalTask, self)._approve_task()


    def _reject_task(self):
        """Reject the transaction"""
        self.ensure_one()
        self.validate_before_approve_or_reject()
        self.set_reject_state()
        return super(AbstractApprovalTask, self)._reject_task()
