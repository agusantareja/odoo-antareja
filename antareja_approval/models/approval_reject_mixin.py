import os
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError
from ..tools.utils import have_method, get_requester_id, to_integer, get_strategy_from_field_name
import requests
import logging

_logger = logging.getLogger(__name__)


class ApprovalStrategyMixin(models.AbstractModel):
    _name = "approval.reject.mixin"

    _description = """
    """
    def action_reject_popup(self):
        return {
            'name': 'Reject Message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'approval.popup.reject.message',
            'target': 'new',
            'context': dict(self.env.context),
        }

    def callback_reject_from_popup_reject(self,reject_reason=None):
        pass
