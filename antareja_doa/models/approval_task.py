# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError
from odoo.models import BaseModel
import logging

_logger = logging.getLogger(__name__)


class ApprovalTask(models.Model):
    _inherit = 'approval.task'

    user_delegation_id = fields.Many2one('user.delegation', compute='_compute_user_delegation')

    def _compute_user_delegation(self):
        for rec in self:
            rec.user_delegation_id = rec.get_user_delegation() or None

    def get_user_delegation(self):
        rec = self.ensure_one()
        delegator_ids = rec.get_users().ids
        return self.env.user.get_delegation(delegator_ids, company_id=rec.company_id)
