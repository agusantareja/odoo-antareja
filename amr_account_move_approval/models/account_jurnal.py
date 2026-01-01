import os

from odoo import models, fields, api
import requests
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ApprovalStrategyConfigStage(models.Model):
    _inherit = "account.journal"

    approval_matrix_id = fields.Many2one(
        'amr.matrix.approval',
        domain=[('form_id', '=', 'account.move')]
    )
