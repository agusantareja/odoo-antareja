import os
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError
from ..tools.utils import have_method, get_requester_id, to_integer, get_strategy_from_field_name
import requests
import logging

_logger = logging.getLogger(__name__)


class ApprovalStrategyInstanceMixin(models.AbstractModel):
    _name = "approval.strategy.instance.mixin"
    _inherit = ["abstract.approval.instance",
                "approval.next.task.able.mixin",
                'approval.transaction.able.mixin',
                'approval.reject.mixin']
    _description = """
    """

    name = fields.Char('Transaction Name', help="Name of the transaction being approved.")
    transaction_model_name = fields.Char('Transaction Model Name')
    description = fields.Text('Description', help="Description of the transaction being approved.")
    company_id = fields.Many2one('res.company', string='Company')
    request_date = fields.Datetime(
        'Request Date', default=fields.Datetime.now,
        help="Date when the approval request was made.")
    requester_id = fields.Many2one(
        'res.users', 'Requester', default=lambda self: self.env.user,
        help="User who requested the approval.")
    is_completed = fields.Boolean()
    stage_status = fields.Char(
        string='Stage Status',
        help="Current The status of the active approval stage.",
    )
    approval_template_instance_id = fields.Many2one(
        'approval.strategy.template.instance',
        string='Approval Template Instance',
        help="Reference to the approval strategy template instance."
    )
    approval_stage_id = fields.Many2one(
        'approval.strategy.stage.mixin',
        help="""Approval stage yang sedang aktif di set di sini.""",
        copy=False
    )
    approval_stages = fields.One2many(
        comodel_name='approval.strategy.stage.mixin',
        inverse_name='approval_instance_id',
        string='Approval Stage',
        help="Tasks of approval stages for the transaction."
    )
    approval_stage_task_ids = fields.Many2many(
        'approval.transaction.task',
        string="Approval Stage Task Active",
        compute='_compute_approval_task_active',
        readonly=True,
        store=False,
    )
    def ensure_approval_template_instance(self):
        if not self.approval_template_instance_id:
            self.approval_template_instance_id = self.approval_template_instance_id.search(
                [('transaction_model_name', '=', self.transaction_model_name)], limit=1)
        return self.approval_template_instance_id

    def get_transaction_object(self):
        return self.env[self.transaction_model_name].browse(self.transaction_id)

    def setup_all_approval_stages(self, config=None):
        if not self:
            return
        self.ensure_one()
        transaction_object = self.get_transaction_object()
        stages = config or self.get_approval_strategy_config(transaction_object=transaction_object)
        for field_name, value in stages.items():
            if not value:
                continue
            status_waiting_approval = value.get('status_waiting_approval', 'waiting_approval')
            stage = self.approval_stages.filtered(lambda s: s.transaction_stage_field == field_name or s.status_waiting_approval == status_waiting_approval)
            if stage:
                continue
            self.create_stage(
                transaction_object=transaction_object,
                config_model=value.get('stage_strategy_config_model_name', 'approval.strategy.config.stage'),
                source=value
            )

    def strategy_button_submit(self):
        """
        Submit to workflow approval
        """
        self.ensure_one()
        config = self.get_approval_strategy_config()
        self.setup_all_approval_stages(config=config)
        self.set_starting_status_approval()
        self.setup_approval_stage(config=config)

    def get_approval_strategy_config(self, transaction_object=None,stage_status=None, **kwargs):
        return self.ensure_approval_template_instance().get_approval_strategy_config(
            transaction_object=transaction_object or self.get_transaction_object(),stage_status=stage_status, **kwargs)

    def prepare_stage_dict(self,
                           transaction_object,
                           transaction_stage_field=None,
                           config={}):
        """Prepare the source dictionary for approval stage creation."""
        self.ensure_one()
        source = {
            'transaction_id': transaction_object.id,
            'transaction_model_name': self.transaction_model_name,
            'name': transaction_object.name,
            'requester_id': to_integer(get_requester_id(transaction_object)),
            'transaction_object':transaction_object
        }
        if config:
            source.update(
                config
            )
        elif transaction_stage_field:
            # strategys = get_strategy_from_field_name(transaction_stage_field)).get(
            # transaction_stage_field, {}
            source.update(
                self.get_approval_strategy_config(transaction_object =transaction_object,transaction_stage_field=transaction_stage_field)
            )
        return source

    def create_stage(self,
                     transaction_object=None,
                     force_create=False,
                     config_model='approval.strategy.config.stage',
                     transaction_stage_field=None,
                     source=None
                     ):
        transaction_object = transaction_object or self.get_transaction_object()
        if transaction_stage_field and transaction_object._fields.get(transaction_stage_field):
            if transaction_stage_field:
                stage = transaction_object[transaction_stage_field]
                if stage and not force_create:
                    return stage
            else:
                if source and source.get('transaction_stage_field', None):
                    transaction_stage_field = source['transaction_stage_field']
                else:
                    raise UserError(_("Transaction stage field is not defined."))

        source = self.prepare_stage_dict(
            transaction_object=transaction_object,
            transaction_stage_field=transaction_stage_field,
            config=source
        )
        context = dict(self.env.context or {})
        try:
            config_model = source.get('stage_strategy_config_model_name', config_model)
            new_object = self.env[config_model].with_context(context).create_new_stage(
                source=source
            )
            new_object.write({
                'approval_instance_id': self.id,
                'transaction_id': transaction_object.id,
                'transaction_model_name': transaction_object._name,
            })
            if transaction_stage_field and transaction_object._fields.get(transaction_stage_field):
                transaction_object.write({
                    transaction_stage_field: new_object.id
                })
            return new_object
        except ShowWizardFormError as e:
            raise e

    def update_stage(self,
                     transaction_object=None,
                     config_model='approval.strategy.config.stage',
                     transaction_stage_field=None):
        """Update the stage configuration."""
        self.ensure_one()
        transaction_object = transaction_object or self.get_transaction_object()
        data = transaction_object[transaction_stage_field]
        approval_stage_id = data.id
        approval_stage_model_name = data._name
        source = self.prepare_stage_dict(
            transaction_object=transaction_object,
            transaction_stage_field=transaction_stage_field)
        source.update({
            'approval_stage_id': approval_stage_id,
            'approval_stage_model_name': approval_stage_model_name,
        })
        config_model = source.get('stage_strategy_config_model_name', config_model)
        strategy_config = self.env[config_model]
        return strategy_config.edit_form(**source)

    def _compute_approval_task_active(self):
        for order in self:
            order.approval_stage_task_ids = order.approval_stage_task_ids.sudo().search([
                ('approval_stage_id.approval_instance_id', '=', order.id)
            ], order='approval_stage_id, sequence, id'
            )

    def _compute_approval_audit_log_line(self):
        for record in self:
            record.approval_audit_log_line = self.env['approval.audit.log'].sudo().search([
                ('transaction_id', '=', record.id),
                ('transaction_model_name', '=', self._name)
            ])

    def _reject_auto_cancel_approval(self):
        for stage in self.approval_stages:
            stage._reject_auto_cancel_approval()

    def create_stage_for_stage_status(self):
        transaction_object = self.get_transaction_object()
        source = self.get_approval_strategy_config(
            transaction_object=transaction_object,
            stage_status=self.stage_status)
        if source:
            return self.create_stage(
                transaction_object=transaction_object,
                source= list(source.values())[0]
            )
        else:
            return None

    def setup_approval_stage(self, **kwargs):
        """
        Menentukan dan menetapkan approval_stage_id berdasarkan status transaksi
        dan strategi approval yang didefinisikan.
        """
        approval_stage_id = None
        for stage in self.approval_stages:
            if stage.status_waiting_approval == self.stage_status:
                approval_stage_id = stage
                break

        if approval_stage_id is None:
            # If no active approval stage found, we need to find the next stage based on the strategy config
            _logger.info("No active approval stage found, looking for next stage.")
            approval_stage_id =self.create_stage_for_stage_status()

        if approval_stage_id:
            # Start new stage
            self.write({
                'approval_stage_id': approval_stage_id.id
            })
            approval_stage_id.setup_approval_stage()
            if approval_stage_id.status_approval in ['draft', 'waiting']:
                approval_stage_id.set_waiting_approval_state()
            approval_stage_id.check_next_approval_task()
            approval_stage_id.notify_user_next_approval_task()
            self.check_next_approval_task()
        else:
            self.write({
                'approval_stage_id': False,
                "next_approval_task_id": False,
            })

    def action_approve_transaction(self):
        """Approve the transaction."""
        self._approve_transaction()

    def _approve_transaction(self):
        self.ensure_one()
        if self.approval_stage_id:
            approval_stage = self.approval_stage_id
            approval_stage._approve_stage()
        else:
            raise UserError("No active approval stage for approval transaction.")

    def action_reject_transaction(self):
        """Reject the transaction."""
        self.ensure_one()
        if self.approval_stage_id:
            # If no approval stage is set, we can reject inline stages
            return {
                'name': 'Reject Message',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'approval.popup.reject.message',
                'target': 'new',
                'context': dict(self.env.context),
            }
        else:
            raise UserError("No active approval stage.")

    def callback_reject_from_popup_reject(self, reject_reason=None):
        self._reject_transaction()

    def _reject_transaction(self):
        if self.approval_stage_id:
            approval_stage = self.approval_stage_id
            approval_stage._reject_stage()
        else:
            raise UserError("No active approval stage for reject.")

    def get_has_approved_condition(self):
        return self.finish_status_approval == self.stage_status

    def callback_approval_stage_approved(self, approval_stage):
        self.ensure_one()
        self.stage_status = approval_stage.get_next_state_after_approved()
        self.setup_approval_stage()
        self.check_next_approval_task()
        self.get_transaction_object().callback_approval_instance_approved(self)
        if self.get_has_approved_condition():
            self.write({
                'is_completed': True,
            })

    def callback_approval_stage_rejected(self, approval_stage):
        self.ensure_one()
        self.stage_status = approval_stage.status_reject
        if self.stage_status == self.draft_status_approval:
            self._reject_auto_cancel_approval()

        self.get_transaction_object().callback_approval_instance_rejected(self)
        self.write({
            'is_completed': True,
        })

    def set_starting_status_approval(self,state=None):
        """
        Starting status approval
        """
        self.stage_status = state or self.starting_status_approval
        return self.stage_status

    def get_next_approval_task(self):
        self.ensure_one()
        return self.approval_stage_id and self.approval_stage_id.get_next_approval_task()
