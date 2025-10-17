from ..tools.utils import to_integer
from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class AbstractApprovalAuditLog(models.AbstractModel):
    _name = 'abstract.approval.audit.log'
    _description = 'Approval Audit Log'
    _order = 'create_date desc'

    name = fields.Char('Name')
    description = fields.Char()
    request_date = fields.Date()
    requester_id = fields.Integer(
        'Requester ID'
    )
    transaction_id = fields.Integer(
        'Transaction ID'
    )
    transaction_model_name = fields.Char(
        'Transaction Model Name',
    )
    inline_approval_task_id = fields.Integer(
        'Inline Approval Task ID',
        help="ID of the approval transaction this log belongs to"
    )
    inline_approval_task_model_name = fields.Char(
        'Approval Model Name')
    inline_approval_task_ref = fields.Reference(
        string='Inline Approval Task Ref',
        selection="_selection_tasks_models",
        compute='_compute_inline_approval_task_ref',
        store=False
    )

    @api.model
    def _selection_tasks_models(self):
        """
        Mengambil model yang valid untuk dijadikan referensi.
        Bisa disaring sesuai kebutuhan (misal hanya model dengan field 'name').
        """
        models = self.env['ir.model'].search([('transient', '=', False)])
        # Filter hanya model yang punya field 'name'
        valid_models = []
        for m in models:
            try:
                valid_models.append((m.model, m.name))
            except:
                continue
        return valid_models

    @api.depends('inline_approval_task_model_name', 'inline_approval_task_id')
    def _compute_inline_approval_task_ref(self):
        for record in self:
            if record.inline_approval_task_model_name and record.inline_approval_task_id:
                inline_approval_task_id = to_integer(record.inline_approval_task_id)
                record.inline_approval_task_ref = f"{record.inline_approval_task_model_name},{inline_approval_task_id}"
            else:
                record.inline_approval_task_ref = False

    approval_instance_id = fields.Many2one(
        'abstract.approval.instance',
        'Approval Instance',
        help="ID of the approval transaction this log belongs to"
    )
    approval_stage_id = fields.Many2one(
        'abstract.approval.stage',
        'Approval Stage ID',
        help="ID of the approval transaction this log belongs to"
    )
    approval_task_id = fields.Many2one(
        'abstract.approval.task',
        help="ID of the approval transaction this log belongs to"
    )

    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user, required=True)
    # proxy_user_id = fields.Many2one('res.users', string="Acting User")
    # delegator_user_id = fields.Many2one('res.users', string="On Behalf Of")
    # user_delegate_id = fields.Many2one('user.delegate')

    action_type = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('proxy_approve', 'Proxy Approve'),
        ('proxy_reject', 'Proxy Reject'),
    ], required=True)
    notes = fields.Text()
    create_date = fields.Datetime(string='Action Time', readonly=True)


class ApprovalAuditLog(models.Model):
    _name = 'approval.audit.log'
    _inherit = ['abstract.approval.audit.log',
                'approval.transaction.able.mixin']
    _description = 'Approval Audit Log'
    _order = 'create_date desc'

    approval_instance_id = fields.Many2one(
        'approval.transaction.instance',
        'Approval Instance',
        help="ID of the approval instance this log belongs to"
    )
    approval_stage_id = fields.Many2one(
        'approval.transaction.stage',
        'Approval Stage',
        help="ID of the approval stage this log belongs to"
    )
    approval_task_id = fields.Many2one(
        'approval.transaction.task',
        help="ID of the approval task this log belongs to"
    )

    def get_transaction_object(self):
        if not self.transaction_id or not self.transaction_model_name:
            return False
        """Get the parent document ID if available."""
        # This method should be overridden in child classes if needed
        return self.env[self.transaction_model_name].browse(self.transaction_id)

    def get_approval_stage_object(self):
        """Get the parent document ID if available."""
        if not self.approval_stage_id or not self.approval_stage_model_name:
            return False
        # This method should be overridden in child classes if needed
        return self.env[self.approval_stage_model_name].browse(self.approval_stage_id)

    def send_message(self):
        rec = self.ensure_one()
        if self.approval_task_id:
            if rec.action_type == 'reject':
                message = self.approval_task_id.get_reject_comment_message()
            elif rec.action_type == 'approve':
                message = self.approval_task_id.get_approved_comment_message()
            else:
                return
            self.approval_task_id.notify_transaction_comment(message=message)

    def create_audit_log(self, without_send_message=False, **kwargs):
        _field = self._fields
        create_dict = {key: value for key, value in kwargs.items() if key in _field}
        ignored_keys = [key for key in kwargs if key not in _field]
        if ignored_keys:
            _logger.warning("Ignored unknown fields in audit log: %s", ignored_keys)
        result = self.create([create_dict])[0]
        if not without_send_message:
            result.send_message()
        return result
