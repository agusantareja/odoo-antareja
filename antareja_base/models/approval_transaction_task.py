# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class ApprovalTransactionTask(models.AbstractModel):
    _name = "approval.transaction.task.able.mixin"

    approval_line_for_document = fields.Many2many(
        'approval.audit.log',
        string='Approval Line for Document',
        compute='_compute_approval_line_for_document',
        help="Approval line untuk di pakai di dokument lembar pengesahan"
    )
    def _compute_approval_line_for_document(self):
        for rec in self:
            rec.approval_line_for_document = rec.approval_line_for_document.get_approval_line_for_document(
                self._name,
                rec.id
            )

    def done_approval_transaction_task(self, **kwargs):
        """
        Approval task as done
        """
        self.ensure_one()
        approval = self.get_approval_transaction_task()
        if approval:
            approval.approval_done(**kwargs)

        if kwargs.get("skip_create_approval_log"):
            return
        self.create_approval_log(**kwargs)

    def setup_approval_transaction_task(self, **kwargs):
        """
        Register to approval task system
        """
        self.ensure_one()
        transaction_id = self.id
        transaction_model_name = self._name
        kw = dict(kwargs)

        if 'name' not in kw:
            kw['name'] = self.display_name

        return self.env['approval.task'].approval_setup(
            transaction_id, transaction_model_name, **kw
        )

    def get_approval_transaction_task(self):
        return self.env['approval.task'].search([
            ('transaction_id', '=', self.id),
            ('transaction_model_name', '=', self._name),
        ], limit=1)

    def send_notification_approval(self, **kwargs):
        approval = self.get_approval_transaction_task()
        if approval:
            approval.send_notification(**kwargs)

    def create_approval_log(self, **kwargs):
        self.ensure_one()
        create_d = dict(kwargs)
        create_d['transaction_id'] = self.id
        create_d['transaction_model_name'] = self._name
        return self.env['approval.audit.log'].create_audit_log(**create_d)

    def unlink(self):
        list_ids = self.ids
        model_name = self._name
        result = super(ApprovalTransactionTask, self).unlink()
        self.env['approval.task'].search(
            [('transaction_model_name', '=', model_name), ('transaction_id', 'in', list_ids)]).unlink()
        return result
