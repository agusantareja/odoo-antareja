# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime

class ProposalManagementWizard(models.TransientModel):
    _inherit = 'proposal_management.wizard'



    def action_approve(self, obj):
        super(ProposalManagementWizard,self).action_approve(obj)
        obj.register_approval_task()
