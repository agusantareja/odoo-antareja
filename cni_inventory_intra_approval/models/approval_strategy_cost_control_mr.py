import os
from odoo import models, fields, api, _
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
# constants for strategy configuration
_strategy_config_name = "cost_control_mr"
_transaction_stage_field = 'stage_' + _strategy_config_name + '_id'


class ApprovalStrategyConfig(models.TransientModel):
    _name = "approval.strategy.config.stage." + _strategy_config_name
    _inherit = "approval.strategy.config.stage"
    _table = "approval_strategy_config_stage"

    _description = """
    
    Helper for create new Approval Cost Control MR Config
    not add persistent data in this model, add at `approval.strategy.config.stage` model.
    
    """

    def validate_approval_before_approve(self, transaction_object, approval_stage_object):
        rec = transaction_object
        if not rec.line_ids:
            raise UserError("Product Harus Diisi")
        for line in rec.line_ids:
            if rec.company_id.id not in [7, 8]:
                if not line.cost_center:
                    raise UserError("Mohon lengkapi cost code")

    def execution_after_approved(self, transaction_object, approval_stage_object):
        transaction_object.write({
                'approver_cost_control': self.env.user.id,
                'flag_cost_control': True
            })

    def execution_after_rejected(self, transaction_object, approval_stage_object):
        message = "Note Reject => %s" % (self.env.context.get('__reject_reason'))
        # mail bot
        transaction_object.write({
            'flag_note': True,
            'notes': message + " by " + str(self.env.user.partner_id.name)
        })
