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


class ProposalManagementApprove(models.Model):
    _name = 'proposal_management.approve'
    _inherit = [_name, 'abstract.approval.access', 'approval.transaction.view.able.mixin', 'approval.task.line.mixin', ]

    approval_audit_log_id = fields.Many2one('approval.audit.log')

    # implemant untuk 'abstract.approval.access'
    user_id = fields.Many2one('res.users', related='validating_users')
    responsible_user_id = fields.Many2one('res.users', related='user_id')

    # implemant untuk approval.transaction.view.able.mixin
    transaction_id = fields.Integer(compute="compute_transaction_model_name", store=True)
    transaction_model_name = fields.Char(compute="compute_transaction_model_name", store=True)

    def get_transaction_object(self):
        return self.proposal_management_id or super(ProposalManagementApprove, self).get_transaction_object()

    @api.depends('proposal_management_id')
    def compute_transaction_model_name(self):
        for rec in self:
            rec.transaction_id = rec.proposal_management_id.id
            rec.transaction_model_name = rec.proposal_management_id._name

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
            'state': 'waiting_approve'
        })

    def domain_waiting_status(self):
        return [('state', '=', 'waiting_approve')]

    def write(self, vals):
        result = super(ProposalManagementApprove, self).write(vals)
        if vals.get('state'):
            for rec in self:
                rec.state == 'approved' and rec.create_audit_log()

        return result

    def create_audit_log(self, create_date=None, user_id=None):
        rec = self
        transaction_object = rec.get_transaction_object()
        if transaction_object:
            al = self.create_approval_audit_log_approved(
                transaction_object=transaction_object,
                transaction_id=transaction_object.id,
                transaction_model_name=transaction_object._name,
                user_id=user_id and int(user_id) or rec.user_id.id,
                name='Approval',
                action_type='approve',
                create_date=create_date or fields.Datetime.now(),
            )
            rec.write({'approval_audit_log_id': al.id})
            return al


    # _order = 'seq, id'
    #
    # proposal_management_id = fields.Many2one('proposal.management')
    # seq = fields.Integer(string='Sequence')
    # validating_users = fields.Many2one('res.users', string='User Approve')
    # job_id = fields.Many2one('hr.job', string='Jabatan')
    # date = fields.Date(string='Date')
    # validation_status = fields.Boolean(string='Approved', readonly=True, default=False, track_visibility='always',
    #                                    help="Status")
    # state = fields.Selection([
    #     ('waiting_approve', 'Waiting Approve'),
    #     ('hold', 'Hold'),
    #     ('approve', 'Approve'),
    # ], string='Status', track_visibility='always', readonly=True, default='waiting_approve')
    # note = fields.Text(string='Note', help="Note")
    #



