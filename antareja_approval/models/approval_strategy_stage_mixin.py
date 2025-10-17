# -*- coding: utf-8 -*-

from .abstract_approval_stage import APPROVAL_STATUS_LIST, APPROVAL_STATUS_APPROVED, \
    APPROVAL_STATUS_REJECTED, APPROVAL_STATUS_CANCELLED
from odoo.addons.antareja_approval.models.abstract_approval_stage import APPROVAL_STATUS_NOT_APPROVE
from odoo.addons.antareja_approval.tools.utils import to_integer, have_method

from odoo import models, fields, api
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ApprovalStrategyStageMixin(models.AbstractModel):
    _name = "approval.strategy.stage.mixin"
    _inherit = ["abstract.approval.stage", 'approval.next.task.able.mixin', 'approval.reject.mixin','approval.transaction.able.mixin']

    state = fields.Selection(
        APPROVAL_STATUS_LIST, related='status_approval',
        string='State',
        help="Current state of the approval transaction."
    )
    approval_instance_id = fields.Many2one(
        'approval.strategy.instance.mixin',
        string='Approval Instance',
        help="Reference to the approval transaction instance."
    )

    def validate_approval_before_approve(self):
        if self.stage_strategy_config_model_name:
            self.env[self.stage_strategy_config_model_name].validate_approval_before_approve(
                self.get_transaction_object(),
                self
            )
        else:
            _logger.warning(
                "No stage strategy config model defined for %s, skipping validation.",
                self._name
            )
    def get_next_state_after_approved(self):
        status_approved = self.status_approved
        if self.stage_strategy_config_model_name:
            stage_strategy = self.env[self.stage_strategy_config_model_name]
            if have_method(stage_strategy,'get_next_state_after_approved'):
                status_approved = stage_strategy.get_next_state_after_approved(
                    self.get_transaction_object(),
                    self
                ) or status_approved

        return status_approved

    def execution_after_approved(self):
        if self.stage_strategy_config_model_name:
            self.env[self.stage_strategy_config_model_name].execution_after_approved(
                self.get_transaction_object(),
                self
            )
        else:
            _logger.warning(
                "No stage strategy config model defined for %s, execution_after_approved.",
                self._name
            )

    def execution_after_rejected(self):
        if self.stage_strategy_config_model_name:
            return self.env[self.stage_strategy_config_model_name].execution_after_rejected(
                self.get_transaction_object(),
                self
            )
        else:
            _logger.warning(
                "No stage strategy config model defined for %s, execution_after_reject.",
                self._name
            )

    def get_transaction_object(self):
        self.ensure_one()
        """Get the transaction document ID if available."""
        transaction_id = self.transaction_id
        transaction_model_name = self.transaction_model_name
        # This method should be overridden in child classes if needed
        return self.env[transaction_model_name].browse(to_integer(transaction_id))


    def setup_approval_stage(self):
        self.ensure_one()
        if self.stage_strategy_inline:
            self.capture_inline_approval_task()

        if self.status_approval not in [APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED, APPROVAL_STATUS_CANCELLED]:
            self.set_waiting_state()

        self.approval_tasks.setup_approval_task()

    def set_waiting_approval_status(self):
        super().set_waiting_approval_status()

    def capture_inline_approval_task(self):
        obj = self.get_transaction_object()
        self.approval_tasks = [(3, task.id)
                               for task in self.approval_tasks if task.is_not_link_with_inline()
                               and task.status_approval not in [APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED, APPROVAL_STATUS_CANCELLED]]
        self.env[self.stage_strategy_inline_model_name].capture_inline_approval_task_to_stage(obj,self)

    def callback_reject_from_popup_reject(self, reject_reason=None):
        approval = self.check_next_approval_task()
        if approval:
            approval.callback_reject_from_popup_reject(reject_reason)
        else:
            self.callback_approval_task_rejected()

    connected_to_transaction = fields.Boolean(compute="_compute_connected_to_transaction")

    def _compute_connected_to_transaction(self):
        for rec in self:
            rec._compute_connected_to_transaction = rec.is_used_by_transaction()

    def is_used_by_transaction(self, transaction_object=None):
        if not self:
            return False
        self.ensure_one()
        transaction_object = transaction_object or self.get_transaction_object()
        if transaction_object and self.transaction_stage_field:
            data = getattr(transaction_object, self.transaction_stage_field, False)
            return data and to_integer(data) == self.id

    def _reject_auto_cancel_approval(self):
        domain = self.get_domain_approval_task()
        approval_tasks = self.approval_tasks.search(domain)
        if approval_tasks:
            approval_tasks.write({
                'status_approval': APPROVAL_STATUS_CANCELLED,
                'reason_approval': 'Approval automatically cancelled due to rejection of the transaction.'
            })

    def action_approve_stage(self):
        self._approve_stage()

    def action_reject_stage(self):
        self._reject_stage()

    def _approve_stage(self):
        self.ensure_one()
        # self.validate_approval_before_approve(
        #     self.get_transaction_object()
        # )
        approval = self.check_next_approval_task()
        if approval:
            approval._approve_task()
        elif self.get_has_approved_condition():
            self.callback_approval_task_approved()
        elif self.get_has_reject_condition():
            self.callback_reject_from_popup_reject()
        else:
            raise UserError("Approval Task Not found.")

        return approval

    def callback_approval_task_approved(self, task_approval=None):
        approval_task_model_name = None
        if task_approval:
            approval_task_model_name = task_approval._name
        if self.get_has_approved_condition(approval_task_model_name=approval_task_model_name):
            self.write({
                'status_approval': APPROVAL_STATUS_APPROVED
            })
            self.check_next_approval_task()
            self.execution_after_approved()
            if self.approval_instance_id:
                self.approval_instance_id.callback_approval_stage_approved(self)
            else:
                self.get_transaction_object().callback_approval_stage_approved(self)
        else:
            next_approval = self.check_next_approval_task()
            if task_approval.id != next_approval.id:
                self.notify_user_next_approval_task()
                if self.approval_instance_id:
                    self.approval_instance_id.check_next_approval_task()
                else:
                    self.get_transaction_object().check_next_approval_task()

    def _reject_stage(self):
        self.ensure_one()
        approval = self.check_next_approval_task()
        if approval:
            approval._reject_task()
        else:
            self.callback_approval_task_rejected()

        return approval

    def callback_approval_task_rejected(self, task_approval=None):
        approval_task_model_name = None
        if task_approval:
            approval_task_model_name = task_approval._name
        if self.get_has_reject_condition(approval_task_model_name=approval_task_model_name):
            self.write({
                'status_approval': APPROVAL_STATUS_REJECTED
            })
            self.execution_after_rejected()
            if self.approval_instance_id:
                self.approval_instance_id.callback_approval_stage_rejected(self)
            else:
                self.get_transaction_object().callback_approval_stage_rejected(self)
        else:
            if self.approval_instance_id:
                self.approval_instance_id.check_next_approval_task()
            else:
                self.get_transaction_object().check_next_approval_task()

    def notify_user_next_approval_task(self):
        self.ensure_one()
        """Notify the user about the approval status."""
        # This method can be overridden in child classes to implement custom notification logic
        # For example, sending an email or a message to a chat channel
        next_approval = self.get_next_approval_task()
        if not next_approval:
            return
        next_approval.notify_user_approval_task()

        return next_approval

    def get_all_approval_tasks(self, approval_task_model_name=None):
        self.ensure_one()
        if not approval_task_model_name:
            approval_task_model_name = self.approval_tasks._name
        return self.env[approval_task_model_name].search([
            ('approval_stage_id', '=', to_integer(self.id)),
            ('approval_stage_model_name', '=', self._name)
        ])

    def get_has_approved_condition(self, approval_task_model_name=None):
        return all(line.status_approval == APPROVAL_STATUS_APPROVED for line in self.approval_tasks)

    def get_has_reject_condition(self, approval_task_model_name=None):
        return any(line.status_approval == APPROVAL_STATUS_REJECTED for line in self.approval_tasks)

    def get_has_waiting_approval_condition(self, approval_task_model_name=None):
        return any(line.status_approval == APPROVAL_STATUS_NOT_APPROVE for line in self.approval_tasks)

    def get_approval_stage_object(self):
        return self

    def get_domain_approval_task(self):
        return [
            ('status_approval', 'in', [False,'draft','waiting',APPROVAL_STATUS_NOT_APPROVE]),
            ('approval_stage_id', '=', self.id),
            # ('approval_stage_model_name', '=', self._name)
        ]

    def get_next_approval_task(self, approval_task_model_name=None):
        self.ensure_one()
        # if not approval_task_model_name:
        #     approval_task_model_name = self.approval_tasks._name
        domain = self.get_domain_approval_task()
        return self.approval_tasks.search(domain, limit=1)
