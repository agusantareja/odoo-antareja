# -*- coding: utf-8 -*-

from ..tools.utils import to_integer
from odoo import models, fields, tools, api
from odoo.addons.antareja_approval.models.abstract_approval_stage import APPROVAL_STATUS_NOT_APPROVE


class ApprovalTransactionTask(models.Model):
    _name = "approval.transaction.task"
    _inherit = 'approval.strategy.task.mixin'
    _description = """
    Approval Transaction Data Waiting Approval Task Approval for user
    """

    notification_to_user_id = fields.Many2one(
        'res.users', string='Notification to User',
        compute="_compute_notification_to_user_id",
        help="User who will receive the notification.",
    )
    @api.depends_context('notification_to_user')
    def _compute_notification_to_user_id(self):
        for rec in self:
            rec.notification_to_user_id = self.env.context.get('notification_to_user')
    sequence = fields.Integer(
        default=10, string='Sequence',
        help="Sequence of the approval line in the transaction"
    )
    approval_stage_id = fields.Many2one(
        'approval.transaction.stage',
        'Approval Stage ID',
        help="ID of the approval stage associated with this transaction"

    )
    approval_instance_id = fields.Many2one(
        'approval.transaction.instance',
        related='approval_stage_id.approval_instance_id'
    )
    approval_stage_model_name = fields.Char(default='approval.transaction.stage')

    internal_url = fields.Char(
        string='Internal URL',
        compute='_compute_internal_url',
        help="Internal URL of the transaction."
    )
    start_amount = fields.Float("Limit/Start Amount")
    @api.depends('transaction_model_name', 'transaction_id')
    def _compute_internal_url(self):
        for rec in self:
            rec.internal_url = rec.get_transaction_object().get_internal_url()

    def get_approval_stage_object(self):
        return self.approval_stage_id

    def name_get(self):
        result = []
        for rec in self:
            if rec.user_id:
                display = f"[{rec.type_approval}] {rec.user_id.name}"
            else:
                display = f"[{rec.type_approval}] [{rec.group_id.name}"
            result.append((rec.id, display))
        return result

    def create(self, vals_list):
        result = super(ApprovalTransactionTask, self).create(vals_list)
        for record in result:
            if record.approval_stage_id:
                # if not record.approval_stage_model_name:
                #     record.approval_stage_model_name = record.approval_stage_id._name
                # record.approval_stage_ref="%s,%s"%(record.approval_stage_model_name,record.approval_stage_id)
                if not record.transaction_id:
                    record.transaction_id = record.approval_stage_id.transaction_id
                if not record.transaction_model_name:
                    record.transaction_model_name = record.approval_stage_id.transaction_model_name
        return result

    def write(self, vals):
        super(ApprovalTransactionTask, self).write(vals)
        if 'approval_stage_id' in vals and vals.get('approval_stage_id') and self.approval_stage_id:
            if self.env.context.get('__skip_approval_task_setup', False):
                return True
            self.with_context(__skip_approval_task_setup=True).write(dict(
                approval_stage_model_name=self.approval_stage_id._name,
                transaction_id=self.approval_stage_id.transaction_id,
                transaction_model_name=self.approval_stage_id.transaction_model_name,
            ))
        return True

    def is_used_by_transaction(self, transaction_object=None):
        return self.ensure_one().approval_stage_id.is_used_by_transaction(transaction_object)

    inline_approval_task_id = fields.Integer()
    inline_approval_task_model_name = fields.Char()
    inline_approval_task_ref = fields.Reference(
        string='inline_approval_task Ref',
        selection="_selection_inline_approval_task_models",
        compute='_compute_inline_approval_task_ref',
        store=False,
        copy=False
    )

    @api.model
    def _selection_inline_approval_task_models(self):
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
        env = self.env
        """Hitung field Reference dari model name dan ID"""
        for record in self:
            model = record.inline_approval_task_model_name
            res_id = record.inline_approval_task_id
            if model and model in env and res_id:
                record_ok = env[model].browse(res_id).exists()
                if record_ok:
                    record.inline_approval_task_ref = f"{model},{res_id}"
            else:
                record.inline_approval_task_ref = False

    def after_approve_task(self):
        super(ApprovalTransactionTask, self).after_approve_task()
        if self.inline_approval_task_ref:
            self.inline_approval_task_ref._approve_task()

    def after_reject_task(self):
        if self.inline_approval_task_ref:
            self.inline_approval_task_ref._reject_task()
        super(ApprovalTransactionTask, self).after_reject_task()

    def action_fix_status(self):
        for rec in self:
            trx = rec.get_transaction_object()
            if rec.status_approval== APPROVAL_STATUS_NOT_APPROVE:
                if trx and trx.next_approval_task_id.id != rec.id:
                    rec.status_approval='waiting'

    def is_not_link_with_inline(self):
        return not(self.inline_approval_task_ref.is_link_with_transaction())

    def prepare_dict_audit_trial(self):
        prepare_dict = super(ApprovalTransactionTask, self).prepare_dict_audit_trial()
        if self.inline_approval_task_id and self.inline_approval_task_model_name:
            prepare_dict.update({
                'inline_approval_task_id': self.inline_approval_task_id,
                'inline_approval_task_model_name': self.inline_approval_task_model_name,
            })

        if 'description' not in prepare_dict:
            prepare_dict['description'] = self.approval_instance_id.description or self.approval_stage_id.description
        if 'requester_id' not in prepare_dict:
            prepare_dict['requester_id'] = to_integer(self.approval_instance_id.requester_id) or to_integer(self.approval_stage_id.requester_id)
        if 'request_date' not in prepare_dict:
            prepare_dict['request_date'] = self.approval_instance_id.request_date or self.approval_stage_id.request_date

        return prepare_dict

    def prepare_approval_task_dict(self):
        """Prepare dict untuk create record approval task"""
        self.ensure_one()
        prepare_dict = super(ApprovalTransactionTask, self).prepare_approval_task_dict()

        if 'description' not in prepare_dict:
            prepare_dict['description'] = self.approval_instance_id.description or self.approval_stage_id.description
        if 'requester_id' not in prepare_dict:
            prepare_dict['requester_id'] = to_integer(self.approval_instance_id.requester_id) or to_integer(
                self.approval_stage_id.requester_id)
        if 'request_date' not in prepare_dict:
            prepare_dict['request_date'] = self.approval_instance_id.request_date or self.approval_stage_id.request_date

        return prepare_dict

    def get_notification_template_approval_task(self, **kwargs):
        template = self.approval_stage_id.notification_template_approval_id
        if template:
            template_model = template.model
            if self.transaction_model_name == template_model and self.transaction_id:
                return template, self.transaction_id
        template, res_id = super().get_notification_template_approval_task(**kwargs)
        return template, res_id

    def get_notification_template_approved_task(self, **kwargs):
        template = self.approval_stage_id.notification_template_approved_id
        if template:
            template_model = template.model
            if self.transaction_model_name == template_model and self.transaction_id:
                return template,self.transaction_id
        template, res_id = super().get_notification_template_approved_task(**kwargs)
        return template, res_id

    def get_notification_template_rejection_task(self,**kwargs):
        template = self.approval_stage_id.notification_template_rejection_id
        if template:
            template_model = template.model
            if self.transaction_model_name == template_model and self.transaction_id:
                return self.transaction_id
        template, res_id = super().get_notification_template_rejection_task(**kwargs)
        return template, res_id
