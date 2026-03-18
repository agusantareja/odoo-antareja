import os
from odoo import models, fields, api, _
from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError
from odoo.addons.antareja_approval.tools.utils import have_method
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_strategy_config_name = "inline_cr"
_transaction_stage_field = 'stage_' + _strategy_config_name + '_id'


class ApprovalStrategyConfig(models.TransientModel):
    _name = "approval.strategy.config.stage." + _strategy_config_name
    _inherit = "approval.strategy.config.stage"
    _table = "approval_strategy_config_stage"

    _description = """
        Helper for create mir inline stage

        not add prsistent data ini this model, 
        add field at `approval.strategy.config.stage` model only.
        """

    def validate_approval_before_approve(self, transaction_object, approval_stage_object):
        pass

    @api.model
    def execution_after_approved(self, transaction_object, approval_stage_object):
        # if not transaction_object.mr_id:
        #     transaction_object.action_create_material_requsition()
        # else:
        #     transaction_object.action_update_material_requsition()
        pass

    def execution_after_rejected(self, transaction_object, approval_stage_object):
        # transaction_object.leave_approval_ids=False
        # transaction_object.append_approval()
        pass
