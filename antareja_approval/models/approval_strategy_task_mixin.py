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
                "approval.task.line.mixin",
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
        self.after_approve_task()

    def after_approve_task(self):
        self.get_approval_stage_object().callback_approval_task_approved(self)
        approval_audit_log = self.create_approval_audit_log_approved()
        approval_audit_log.notification_requestor()

    def callback_reject_from_popup_reject(self, reject_reason=None):
        self._reject_task()

    def action_reject_task(self):
        self._reject_task()

    def _reject_task(self):
        """Reject the transaction"""
        super(ApprovalStrategyTaskMixin, self)._reject_task()
        self.after_reject_task()

    def after_reject_task(self):
        self.get_approval_stage_object().callback_approval_task_rejected(self)
        approval_audit_log = self.create_approval_audit_log_rejected()
        approval_audit_log.notification_requestor()

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
        requester_id = to_integer(get_requester_id(self.get_transaction_object())
                                  or get_requester_id(self.get_approval_stage_object())
                                  or get_requester_id(self))
        return {
            'transaction_id': to_integer(self.transaction_id),
            'transaction_model_name': self.transaction_model_name,
            'approval_stage_id': to_integer(self.approval_stage_id),
            'approval_instance_id': to_integer(self.approval_stage_id.approval_instance_id),
            'approval_task_id': self.id,
            'notes': self.reason_approval,
            'requester_id': requester_id
        }

    def create_approval_audit_log_approved(self,**kwargs):
        rec = self.ensure_one()
        kw = dict(kwargs)
        kw.update(self.prepare_dict_audit_trial())
        kw['action_type']='approve'
        notification_template, notification_res_id= rec.get_notification_template_approved_task(**kwargs)
        if notification_template:
            kw['notification_template_id']=notification_template.id
            kw['notification_res_id'] = notification_res_id
        self.approval_audit_log_id = super(ApprovalStrategyTaskMixin,self).create_approval_audit_log_approved(**kw)
        return self.approval_audit_log_id

    def create_approval_audit_log_rejected(self, **kwargs):
        rec = self.ensure_one()
        kw = dict(kwargs)
        kw.update(rec.prepare_dict_audit_trial())
        kw['action_type'] = 'reject'
        notification_template, notification_res_id = rec.get_notification_template_rejection_task(**kwargs)
        if notification_template:
            kw['notification_template_id'] = notification_template.id
            kw['notification_res_id'] = notification_res_id
        self.approval_audit_log_id = super(ApprovalStrategyTaskMixin, self).create_approval_audit_log_rejected(**kw)
        return self.approval_audit_log_id


    def get_users_for_notify_approval_task(self):
        """Get the users for approval task."""
        return self.get_users()

    def notify_user_approval_task(self, **kwargs):
        rec = self.ensure_one()
        kwargs = dict(kwargs)
        kwargs['rec_object'] = self
        users =rec.get_users_for_notify_approval_task()
        if self.env.context.get('__ignore_notify_approval_by_users') or not users:
            return
        template, res_id = rec.get_notification_template_approval_task(**kwargs)
        if template:
            template.send_notification_to_users(users,res_id)
        else:
            _logger.warning("No notification template found for approval notification.")
        return rec


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

    def setup_approval_task_manager(self,**kwargs):
        kw = dict(kwargs)
        kw.update(self.prepare_approval_task_dict())
        self.env['approval.task'].approval_setup(
            transaction_id=self.transaction_id,
            transaction_model_name=self.transaction_model_name,
            **kw
        )
