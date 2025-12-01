# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))

class ApprovalAuditLog(models.Model):
    _name = 'approval.audit.log'
    _inherit = 'approval.transaction.able.mixin'
    _description = 'Approval Audit Log'
    _order = 'create_date desc'

    name = fields.Char('Name')
    user_id = fields.Many2one(
        'res.users',
        "User",
        default=lambda self: self.env.user,
        required=True
    )
    # jika approval berdasarkan group
    group_name = fields.Char()
    job_position = fields.Char()
    delegator_id = fields.Many2one(
        'res.users',
        "Delegator",
        default=lambda self: self.env.user,
        help="User who delegated the approval action"
    )
    delegator_job_position = fields.Char()
    action_type = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('behalf_approve', 'Behalf Approve'),
        ('behalf_reject', 'Behalf Reject'),
        ('proxy_approve', 'Proxy Approve'),
        ('proxy_reject', 'Proxy Reject'),
    ], required=True)
    requestor_id = fields.Many2one(
        'res.users',
        "Requestor Approval",
    )
    notes = fields.Text(
        'Notes',
        help="Additional notes or comments regarding the action reject"
    )
    create_date = fields.Datetime(string='Action Time', readonly=True, default=fields.Datetime.now)

    transaction_display_name = fields.Char(
        'Name',
        compute='_compute_transaction_display_name',
        compute_sudo=True,
    )

    def _compute_transaction_display_name(self):
        for rec in self:
            obj = rec.get_transaction_object()
            rec.transaction_display_name = obj and obj.display_name or rec.name or rec.display_name

    def get_transaction_object(self):
        if not self.transaction_id or not self.transaction_model_name:
            return False
        """Get the parent document ID if available."""
        # This method should be overridden in child classes if needed
        return self.env[self.transaction_model_name].browse(self.transaction_id)

    def create_audit_log(self, **kwargs):
        _field = self._fields
        create_dict = {key: value for key, value in kwargs.items() if key in _field}
        ignored_keys = [key for key in kwargs if key not in _field]
        if ignored_keys:
            _logger.warning("Ignored unknown fields in audit log: %s", ignored_keys)
        return self.create([create_dict])[0]

    def get_approval_line_for_document(self,transaction_model_name, transaction_id,limit=100):
        """Retrieve the approval document based on model name and ID. agar bisa di pakai untuk tanda tangan di dokument"""
        approval_line = self.browse()
        candidate = self.search(
            [('transaction_model_name','=',transaction_model_name),('transaction_id','=',transaction_id)],
            limit=limit,
            order='create_date desc'
        )
        for  rec in candidate:
            if rec.action_type in ['reject','behalf_reject','proxy_reject']:
                # stop on first reject
                # asusmi saat terjadi reject maka approval di reset ulang
                break
            approval_line += rec

        if approval_line:
            # reverse
            approval_line = approval_line[::-1]
        return approval_line

    def notification_requestor(self,**kwargs):
        raise NotImplementedError("Notification Requestor Not Implementation")
