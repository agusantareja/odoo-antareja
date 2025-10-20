import os


from odoo import models, fields, api
import requests
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ApprovalStrategyConfigStage(models.Model):
    _inherit = "account.journal"

    approval_template_id = fields.Many2one(
        'approval.strategy.template.instance'
    )
