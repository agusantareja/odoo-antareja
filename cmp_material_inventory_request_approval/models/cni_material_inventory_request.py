# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)

class CniMaterialIssueRequest(models.Model):
    _name = 'material.inventory.request'
    _inherit = [_name,'cni.approval.transaction.task.able.mixin']

    def register_approval_task(self, **kwargs):
        kw = dict(kwargs)
        if 'requester_id' not in kw:
            kw['requester_id'] =self.request_by.user_id.id

        return super(CniMaterialIssueRequest,self).register_approval_task(**kw)

    def button_request_approval(self):
        rec = self.ensure_one()
        rec.action_request_approval()
        # self.approval_ids = False
        # self.env['cni.matrix.approval.line'].request_by_value(self, self.total_value,
        #     self.company_currency_id, 'material inventory request', self.request_by.user_id.id)

    def event_approval_start(self):
        if self.is_intercompany:
            self.write({'request_status':'intercompany_approval', 'flag_reject': False})
        else:
            self.write({'request_status':'waiting', 'flag_reject': False})

    def button_approve_approval(self):
        rec = self.ensure_one()
        rec.action_approve()

    def event_approval_done(self,is_approved=False):
        # if approval_sts == 0:
        if is_approved:
            self.write({
                'approved_by': self.approved_by or self.env.uid,
                'approved_date': self.approved_date or fields.Date.context_today(self),
                'completed_by': None,
                'completed_date': None,
                'picked_by': None,
                'picked_date': None,
                'request_status': 'approved'
            })
            self._approve()  # mungkin nanti diganti _picking()


