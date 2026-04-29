# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime
import xlrd
import requests
import json
import base64
import tempfile
import binascii
import logging

_logger = logging.getLogger(__name__)


class TravelApproval(models.Model):
    _name = 'travel.approval'
    _inherit = [_name,'abstract.approval.access','approval.transaction.view.able.mixin','approval.task.line.mixin',]
    _order = 'seq,id'

    approval_audit_log_id = fields.Many2one('approval.audit.log')

    # implemant untuk 'abstract.approval.access'
    user_id = fields.Many2one('res.users', related='employee_id.user_id')
    responsible_user_id = fields.Many2one('res.users', related='employee_id.user_id')

    # implemant untuk approval.transaction.view.able.mixin
    transaction_id = fields.Integer(compute="compute_transaction_model_name", store=True)
    transaction_model_name = fields.Char(compute="compute_transaction_model_name", store=True)

    def get_transaction_object(self):
        return self.travel_id or super(TravelApproval, self).get_transaction_object()

    @api.depends('travel_id')
    def compute_transaction_model_name(self):
        for rec in self:
            rec.transaction_id = rec.travel_id.id
            rec.transaction_model_name = rec.travel_id._name

    # implemant untuk approval.task.line.mixin
    def set_approved_status(self, **kwargs):
        self.write({
            'state': 'approved'
        })

    # def set_rejected_status(self, **kwargs):
    #     self.write({
    #         'state': 'reject'
    #     })

    def set_waiting_status(self, **kwargs):
        self.write({
            'state': 'waiting'
        })

    def domain_waiting_status(self):
        return [('state', '=', 'waiting')]


    def write(self, vals):
        result = super(TravelApproval,self).write(vals)
        if vals.get('state'):
            for rec in self:
                rec.state=='approved' and rec.create_audit_log()

        return result

    def create_audit_log(self,create_date=None):
        rec=self
        transaction_object=rec.travel_id
        if transaction_object:
            al = rec.create_approval_audit_log_approved(
                transaction_object=transaction_object,
                transaction_id=transaction_object.id,
                transaction_model_name=transaction_object._name,
                user_id=rec.user_id.id,
                name='Approval',
                create_date=create_date or fields.Datetime.now(),
            )
            rec.write({'approval_audit_log_id': al.id})
            return al

    # travel_id = fields.Many2one('travel.request', string='Travel')
    # job_id = fields.Many2one('hr.job', string='Job position')
    # employee_id = fields.Many2one('hr.employee', string='Employee')
    # state = fields.Selection([
    #     ('waiting', 'Waiting Approval'),
    #     ('approved', 'Approved')
    # ], default='waiting', string='State')
    # seq = fields.Integer(string='Sequence')


