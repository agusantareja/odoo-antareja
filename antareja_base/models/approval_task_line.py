# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError
from odoo.models import BaseModel
import logging

_logger = logging.getLogger(__name__)


class ApprovalTaskLine(models.Model):
    _name = 'approval.task.line'
    _inherit = ['approval.task.line.mixin',
                'abstract.approval.status',
                'abstract.approval.access',
                'approval.transaction.view.able.mixin'
                ]
    _description = 'This is Approval Task Line for Approval helper waiting approval'
    _order = 'create_date desc'
    approval_instance_id = fields.Many2one('approval.instance')
    requester_id = fields.Many2one(
        'res.users', 'Requester',
        default=lambda self: self.env.user,
        help="User who requested the approval."
    )
