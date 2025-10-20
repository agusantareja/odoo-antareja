import os

from odoo import models, fields, api
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


_strategy_config_name = "matrix_tiered"

class ApprovalStrategyConfigStage(models.TransientModel):
    _name = "approval.strategy.config.stage." + _strategy_config_name
    _inherit = ["approval.strategy.config.stage"]
    _table = "approval_strategy_config_stage"
    _description = """
    """

    ########################################################
    def create_new_stage(self, source=None):
        """Create a new approval stage for HR employee."""
        param = {}
        if isinstance(source, dict):
            param.update(source)

        matrix_rule = self.env["approval.matrix.tiered.rule"].get_approval_matrix_rule(**param)
        # requester_id = source.get("requester_id") or self.env.context.get('default_requester_id')
        if matrix_rule:
            source['approval_tasks'] = matrix_rule.get_approval_line(**param)
        else:
            raise UserError("Approval Matrix Tiered Rule not found, please configure Approval Matrix Tiered Rule first.")

        # Create a new stage
        return super(ApprovalStrategyConfigStage, self).create_new_stage(source)

    # ########################################################
    # rule when stage running

    # def validate_approval_before_approve(self, transaction_object, approval_stage_object):
    #     """
    #     Validate approval stages before approving.
    #     This method should be overridden by child models to provide specific
    #     approval validation logic.
    #     """
    #     # Example validation logic
    #     pass
