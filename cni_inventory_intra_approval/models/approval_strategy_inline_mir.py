import os
from odoo import models, fields, api, _
from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError
from odoo.addons.antareja_approval.tools.utils import have_method
import logging

_logger = logging.getLogger(__name__)

# constants for strategy configuration
_strategy_config_name = "inline_mir"
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

    def execution_after_approved(self, transaction_object, approval_stage_object):
        pass

    def execution_after_rejected(self, transaction_object, approval_stage_object):
        message = "Note Reject => %s" % (self.env.context.get('__reject_reason'))
        # mail bot
        transaction_object.write({
            'flag_note': True,
            'notes': message + " by " + str(self.env.user.partner_id.name)
        })
