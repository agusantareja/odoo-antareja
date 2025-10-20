
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ApprovalStrategyTemplateInstance(models.Model):
    _inherit = "approval.strategy.template.instance"

    def get_approval_strategy_template_instance(self, transaction_object=None, **kwargs):
        if not transaction_object or not isinstance(transaction_object, models.BaseModel):
            raise UserError(_("Invalid transaction object provided."))
        transaction_model_name = transaction_object._name
        if "account.move" == transaction_model_name :
            return transaction_object.journal_id.approval_template_id

        return super(ApprovalStrategyTemplateInstance, self).get_approval_strategy_template_instance(transaction_object, **kwargs)
