import os
from odoo import models, fields, api, _
import logging
from odoo.exceptions import ValidationError, UserError
from .abstract_approval_stage import APPROVAL_STATUS_NOT_APPROVE, APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED, \
    APPROVAL_STATUS_CANCELLED, APPROVAL_STATUS_LIST
from ..tools.utils import  to_integer, get_email_template_approval_id, \
    get_mail_bot_template_approval_id, get_whatsapp_template_approval_id, get_requester_id, \
    get_email_template_rejection_id, get_mail_bot_template_rejection_id, get_whatsapp_template_rejection_id

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)




class ApprovalStrategyTaskMixin(models.AbstractModel):
    _name = "approval.strategy.task.mixin"
    _inherit = ["approval.transaction.able.mixin",
                "approval.stage.able.mixin",
                "abstract.approval.task",
                "abstract.approval.access",
                'approval.reject.mixin',
                "approval.notification.task.mixin",
                ]
    _description = """
    Inline adalah strategi handel legacy approval task
    """
    approval_audit_log_id = fields.Many2one('approval.audit.log')

    def setup_approval_task(self):
        records = self.filtered(lambda r: not r.status_approval or r.status_approval == 'draft')
        for rec in records:
            rec.set_waiting_state()

    def action_approve_task(self):
        if self.access_approval:
            self._approve_task()
        else:
            raise ValidationError("You are not authorized to approve this transaction.")


    def _approve_task(self):
        """Approve the transaction"""
        self.approval_stage_id.validate_approval_before_approve()
        super(ApprovalStrategyTaskMixin, self)._approve_task()
        self.create_audit_trial('approve')
        self.after_approve_task()

    def after_approve_task(self):
        self.get_approval_stage_object().callback_approval_task_approved(self)

    def callback_reject_from_popup_reject(self, reject_reason=None):
        self._reject_task()

    def action_reject_task(self):
        self._reject_task()

    def _reject_task(self):
        """Reject the transaction"""
        super(ApprovalStrategyTaskMixin, self)._reject_task()
        self.create_audit_trial('reject')
        self.after_reject_task()

    def after_reject_task(self):
        self.get_approval_stage_object().callback_approval_task_rejected(self)
        self.notify_user_reject_task()

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

    def prepare_dict_audit_trial(self):
        return {
            'transaction_id': to_integer(self.transaction_id),
            'transaction_model_name': self.transaction_model_name,
            'approval_stage_id': to_integer(self.approval_stage_id),
            'approval_instance_id': to_integer(self.approval_stage_id.approval_instance_id),
            'approval_task_id': self.id,
            'notes': self.reason_approval
        }

    def create_audit_trial(self, action_type, ignore_message=False, **kwargs):
        prepare_dict = self.prepare_dict_audit_trial()
        prepare_dict.update(kwargs)
        prepare_dict['action_type'] = action_type
        self.approval_audit_log_id = self.approval_audit_log_id.create_audit_log(
            without_send_message=ignore_message,
            **prepare_dict
        )

        return self.approval_audit_log_id

    def get_users_for_notify_approval_task(self):
        """Get the users for approval task."""
        return self.get_users()

    def notify_user_approval_task(self, **kwargs):
        self.ensure_one()
        kwargs = dict(kwargs)
        kwargs['rec_object'] = self
        self.notify_approval_by_users(self.get_users_for_notify_approval_task(), **kwargs)
        return self

    def notify_user_reject_task(self, **kwargs):
        self.ensure_one()
        requester =  self.env['res.users'].browse(
            to_integer(kwargs.get('requester_id')
                       or get_requester_id(self.get_transaction_object())
                       or get_requester_id(self.get_approval_stage_object())
                       or get_requester_id(self)))
        self.notify_reject_task_user(requester,**kwargs)

    @api.model
    def prepare_dict_for_create(self, **kwargs):
        prepare_dict = dict(kwargs)
        return prepare_dict

    def is_used_by_transaction(self, transaction_object):
        if transaction_object:
            return transaction_object == self.get_transaction_object()
        return True

    def name_get(self):
        result = []
        for rec in self:
            if rec.user_id:
                display = f"[{rec.type_approval}] {rec.user_id.name}"
            elif rec.group_id:
                display = f"[{rec.type_approval}] [{rec.group_id.name}"
            else:
                display = f"[{self._name}] [{rec.id}"
            result.append((rec.id, display))
        return result
