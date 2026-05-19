# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ApprovalTaskLineMixin(models.AbstractModel):
    _inherit = "approval.task.line.mixin"
    _description = "Approval Task Line Integration Mixin"

    user_delegation_id = fields.Many2one('user.delegation',store=False)


