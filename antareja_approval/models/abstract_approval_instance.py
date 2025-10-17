# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.antareja_approval.tools.utils import to_integer, param_transaction_object

from odoo.exceptions import UserError


class AbstractApprovalInstance(models.AbstractModel):
    _name = "abstract.approval.instance"

    transaction_model_name = fields.Char('Transaction Model Name')
    description = fields.Char()
    draft_status_approval = fields.Char(
        string='Draft Status Approval',
        default='draft',
        help="The status of the approval instance when it is in draft state."
    )
    starting_status_approval = fields.Char(
        string='Starting Status Approval',
        default='waiting_approval',
        help="The initial status of the approval instance when it is created."
    )
    finish_status_approval= fields.Char(
        string='Finish Status Approval',
        default='approved',
    )
    approval_stages = fields.One2many(
        'abstract.approval.stage',
        'approval_instance_id',
        string="Approval Stage",
    )
