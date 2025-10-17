# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ApprovalTransactionStage(models.Model):
    _name = "approval.transaction.stage"
    _inherit = ["approval.strategy.stage.mixin"]
    _description = """
    Multi stage approval transaction model.
    This model serves as a base for transactions that require approval.
    It contains the transaction ID and the model name of the transaction.
    It is designed to be inherited by other models that require approval functionality.
    The transaction ID refers to the ID of the parent document that is being approved.
    The transaction model name is the name of the model that contains the parent document.
    This model can be used to track the approval process of various transactions in Odoo.
    """

    active = fields.Boolean(default=True, string="Active")
    approval_instance_id = fields.Many2one(
        'approval.transaction.instance',
        string='Approval Instance',
        help="Reference to the approval transaction instance."
    )
    approval_tasks = fields.One2many(
        comodel_name='approval.transaction.task',
        inverse_name='approval_stage_id',
        string='Approval Tasks',
        help="Tasks of approval stages for the transaction."
    )

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.name}][{rec.state}] {rec.description}"
            result.append((rec.id, display))
        return result

    def action_fix_status(self):
        for rec in self:
            trx = rec.get_transaction_object()
            if rec.status_approval=='waiting_approval':
                if trx and trx.approval_stage_id.id != rec.id:
                    rec.status_approval='waiting'
