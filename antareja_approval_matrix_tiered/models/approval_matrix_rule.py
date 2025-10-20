# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

_logger = __import__('logging').getLogger(__name__)


class ApprovalTieredMatrixRule(models.Model):
    _name = "approval.matrix.tiered.rule"
    _description = """ 
    """
    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name", required=True)
    model = fields.Char("Model")
    context = fields.Char("Context")
    company_id = fields.Many2one('res.company', "Company")
    limit_amount = fields.Float()
    approval_matrix_tiered_rule_line = fields.One2many(
        'approval.matrix.tiered.rule.line','approval_matrix_rule_id'
    )

    # setup when configuration
    def get_approval_matrix_rule(self, **kwargs):
        model = kwargs.get('transaction_model_name')
        context = kwargs.get('transaction_model_context')
        transaction_amount = kwargs.get('transaction_amount')
        company_id = kwargs.get('company_id')
        def get_rule(domain):
            return self.search(domain, order='limit_amount', limit=1)
        return (
                get_rule([('model', '=', model),('limit_amount', '>=', transaction_amount),('context', '=', context),('company_id', '=', company_id)]) or
                get_rule([('model', '=', model),('limit_amount', '>=', transaction_amount),('context', '=', context),('company_id', '=', False)]) or
                get_rule([('model', '=', model), ('limit_amount', '>=', transaction_amount), ('context', '=', False),('company_id', '=', company_id)]) or
                get_rule([('model', '=', model), ('limit_amount', '>=', transaction_amount), ('context', '=', False),('company_id', '=', False)])
                )

    def get_approval_line(self, **kwargs):
        approval_line = []
        if self:
            transaction_amount = kwargs.get('transaction_amount')
            for line in self.approval_matrix_tiered_rule_line:
                if line.start_amount <= transaction_amount:
                    approval_line.append({
                        'type_approval':'multi_group',
                        'group_ids': line.group_ids.ids
                    })
        return approval_line

class ApprovalNotification(models.Model):
    _name = "approval.matrix.tiered.rule.line"
    _description = """
    Mixin : Approval Notification Approval Task Model
    """
    approval_matrix_rule_id = fields.Many2one(
        'approval.tiered.matrix.rule',
        "Approval Matrix Rule",
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer("Sequence", default=10)
    name = fields.Char("Description")
    group_ids = fields.Many2many('res.groups', string="Approval Group")
    start_amount = fields.Float("Start Amount")
