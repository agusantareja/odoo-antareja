import os
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

# constants for strategy configuration
_strategy_config_name = "inline_lr"
_transaction_stage_field = 'stage_' + _strategy_config_name + '_id'


class ApprovalStrategyConfig(models.TransientModel):
    _name = "approval.strategy.config.stage." + _strategy_config_name
    _inherit = "approval.strategy.config.stage"
    _table = "approval_strategy_config_stage"

    _description = """
        Helper for create lr inline stage

        not add prsistent data ini this model, 
        add field at `approval.strategy.config.stage` model only.
        """

    def validate_approval_before_approve(self, transaction_object, approval_stage_object):
        pass

    def execution_after_approved(self, transaction_object, approval_stage_object):
        pass

    def execution_after_rejected(self,transaction_object, approval_stage_object):
        # transaction_object.leave_approval_ids=False
        # transaction_object.append_approval()
        pass
