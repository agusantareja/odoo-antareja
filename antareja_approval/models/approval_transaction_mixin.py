# -*- coding: utf-8 -*-
import json

from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError
from ..tools.notification import to_integer
from odoo import models, fields, api
from lxml import etree
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class AbstractApprovalTransaction(models.AbstractModel):
    _name = "approval.transaction.mixin"
    _inherit = ["approval.next.task.able.mixin","approval.transaction.task.able.mixin"]
    _description = """
    Mixin : Approval Transaction
        """
    state_is_draft = fields.Boolean(string="State is Draft", compute='_compute_state_is_draft')
    approval_instance_id = fields.Many2one(
        'approval.transaction.instance',
        string='Approval Instance',
        help="Reference to the approval transaction instance."
    )

    approval_stage_id = fields.Many2one(
        'approval.transaction.stage',
        related='approval_instance_id.approval_stage_id',
    )
    approval_stage_active = fields.Many2many(
        'approval.transaction.stage',
        string="Approval Stage Active",
        compute='_compute_approval_stage_active',
        readonly=True,
        store=False,
    )

    approval_stage_task_active = fields.Many2many(
        'approval.transaction.task',
        string="Approval Stage Task Active",
        compute='_compute_approval_task_active',
        readonly=True,
        store=False,
    )

    approval_stage_task_line = fields.One2many(
        'approval.transaction.task',
        related='approval_stage_id.approval_tasks',
    )

    approval_audit_log_line = fields.Many2many(
        'approval.audit.log',
        compute='_compute_approval_audit_log_line',
    )
    next_approval_task_id = fields.Many2one(
        related='approval_instance_id.next_approval_task_id',
        string="Next Approval Task", store=False, readonly=True
    )

    def _compute_state_is_draft(self):
        for rec in self:
            rec.state_is_draft = rec.state == 'draft'

    def create_approval_instance(self):
        approval_instance = self.env['approval.strategy.template.instance'].create_approval_instance(self)
        self.write({
            'approval_instance_id': to_integer(approval_instance)
        })
        return approval_instance

    def ensure_approval_instance(self):
        return self.approval_instance_id or self.create_approval_instance()

    def setup_approval_instance(self):
        self.ensure_one()
        if self.approval_instance_id and not self.approval_instance_id.is_completed:
            self.approval_instance_id.write({"is_completed":True})
        self.approval_instance_id = None
        approval_instance= self.ensure_approval_instance()
        self.register_approval_task()
        return approval_instance

    def strategy_button_submit(self):
        self.ensure_one()
        if self.approval_instance_id and self.approval_instance_id.is_completed:
            self.approval_instance_id = None
        try:
            self.ensure_approval_instance().strategy_button_submit()
            self.set_transaction_status(self.approval_instance_id.stage_status)
        except ShowWizardFormError as e:
            return e.get_action_form()

    def _compute_approval_stage_active(self):
        for order in self:
            order.approval_stage_active = order.approval_instance_id.approval_stages

    def _compute_approval_task_active(self):
        for order in self:
            order.approval_stage_task_active = order.approval_instance_id.approval_stage_task_ids

    def _compute_approval_audit_log_line(self):
        for record in self:
            record.approval_audit_log_line = self.env['approval.audit.log'].sudo().search([
                ('transaction_id', '=', record.id),
                ('transaction_model_name', '=', self._name)
            ])

    def get_transaction_status(self):
        """
        Get the transaction status of the approval transaction.
        This method should be overridden by child models to provide specific
        transaction status logic.
        Returns:
            str: The status of the transaction.
        """
        return self.state or 'draft'

    def set_transaction_status(self, status):
        """
        Set the transaction status of the approval transaction.
        This method should be overridden by child models to provide specific
        transaction status logic.
        Args:
            status (str): The new status of the transaction.
        """
        self.write({'state': status})

    def setup_approval_stage(self):
        approval_instance = self.ensure_approval_instance()
        if not approval_instance.is_completed:
            approval_instance.stage_status = self.get_transaction_status()
            approval_instance.setup_approval_stage()

    def action_approve_transaction(self):
        self.ensure_approval_instance().action_approve_transaction()

    def action_reject_transaction(self):
        return self.ensure_approval_instance().action_reject_transaction()

    def callback_reject_from_popup_reject(self, reject_reason=None):
        self.ensure_approval_instance().callback_reject_from_popup_reject(reject_reason=reject_reason)

    def get_next_approval_task(self):
        return self.ensure_approval_instance().get_next_approval_task()

    def callback_approval_instance_approved(self, approval_instance):
        self.set_transaction_status(approval_instance.stage_status)
        self.check_next_approval_task()
        if self.approval_instance_id.get_has_approved_condition() or self.approval_instance_id.is_completed:
            self.unregister_approval_task(skip_create_approval_log=True)


    def callback_approval_instance_rejected(self, approval_instance):
        self.set_transaction_status(approval_instance.stage_status)
        self.approval_instance_id = None
        self.unregister_approval_task(skip_create_approval_log=True)

    def register_approval_task(self, **kwargs):
        kw = dict(kwargs)
        next_approval_task = self.get_next_approval_task()
        if next_approval_task :
            users = self.env['res.users'].browse()
            groups = self.env['res.groups'].browse()
            if next_approval_task.type_approval == 'user' and next_approval_task.user_id:
                users |= next_approval_task.user_id

            elif next_approval_task.type_approval == 'group' and next_approval_task.group_id:
                groups |= next_approval_task.group_id

            elif next_approval_task.type_approval == 'multi_user' and next_approval_task.user_ids:
                users = next_approval_task.user_ids
            elif next_approval_task.type_approval == 'multi_group' and next_approval_task.group_ids:
                groups = next_approval_task.group_ids
            else:
                # === OPSI FALLBACK ===
                if next_approval_task.user_id:
                    users |= next_approval_task.user_id
                if next_approval_task.user_ids:
                    users |= next_approval_task.user_ids
                if next_approval_task.group_id:
                    groups |= next_approval_task.group_id
                if next_approval_task.group_ids:
                    groups |= next_approval_task.group_ids
            if users:
                kw['user_ids'] = users
            if groups:
                kw['group_ids'] = groups
            kw.update({
                'approval_instance_id': self.approval_instance_id.id
            })
            approval_transaction_task = super(AbstractApprovalTransaction, self).register_approval_task(*kw)
            _logger.info("next approval task found for transaction id %s -> %s", self.id, approval_transaction_task)
            return approval_transaction_task
        else:
            _logger.info("No next approval task found for transaction id %s", self.id)
