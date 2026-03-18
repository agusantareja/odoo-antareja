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
        """Create a new approval stage for approval matrix rule."""
        param = {}
        if isinstance(source, dict):
            param.update(source)

        matrix_rule = self.env["approval.matrix.tiered.rule"].get_approval_matrix_rule(**param)
        # requester_id = source.get("requester_id") or self.env.context.get('default_requester_id')
        if matrix_rule:
            if matrix_rule.notification_template_approval_id:
                source['notification_template_approval_id'] = matrix_rule.notification_template_approval_id.id
            if matrix_rule.notification_template_rejection_id:
                source['notification_template_rejection_id'] = matrix_rule.notification_template_rejection_id.id
            if matrix_rule.notification_template_approved_id:
                source['notification_template_approved_id'] = matrix_rule.notification_template_approval_id.id
            source['approval_tasks'] = matrix_rule.get_approval_line(**param)
        else:
            raise UserError(
                "Approval Matrix Tiered Rule not found, please configure Approval Matrix Tiered Rule first.")

        # Create a new stage
        return super(ApprovalStrategyConfigStage, self).create_new_stage(source)
