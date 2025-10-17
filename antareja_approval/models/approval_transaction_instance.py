# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ApprovalTransactionInstance(models.Model):
    _name = "approval.transaction.instance"
    _inherit = ["approval.strategy.instance.mixin", 'approval.reject.mixin',
                ]
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
    approval_stage_id = fields.Many2one(
        'approval.transaction.stage',
    )
    approval_stages = fields.One2many(
        comodel_name='approval.transaction.stage',
        inverse_name='approval_instance_id',
        string='Approval Tasks',
        help="Tasks of approval stages for the transaction."
    )
    approval_tasks = fields.One2many(
        'approval.transaction.task',
        string="Approval Stage Task Active",
        inverse_name='approval_instance_id',
    )
    def capture_stages(self):
        """
        Capture the approval stages defined in the template instance.
        This method is used to create or update the approval stages based on the template.
        """
        t = self.get_transaction_object()
        approval_stages = self.approval_stages.search([
            ('approval_instance_id', '=', False),
            ('transaction_model_name', '=', t._name),
            ('transaction_id', '=', t.id)]
        )
        for stage in approval_stages:
            if stage.is_used_by_transaction(t):
                stage.approval_instance_id = self.id

    def name_get(self):
        result = []
        for rec in self:
            display = f"[{rec.name}] {rec.description}"
            result.append((rec.id, display))
        return result

    def notify_user_next_approval_task(self):
        if self.approval_stage_id:
            self.approval_stage_id.notify_user_next_approval_task()

    def action_fix_status(self):
        for rec in self:
            if not rec.is_completed:
                trx = rec.get_transaction_object()
                if not trx or trx.approval_instance_id.id != rec.id:
                    rec.is_completed = True
