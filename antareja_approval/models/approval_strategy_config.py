import os
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError
from ..tools.utils import have_method, ensure_create_tuples_many2one
import requests
import logging

_logger = logging.getLogger(__name__)


class ApprovalTransactionTask(models.TransientModel):
    _name = "approval.strategy.config.task"
    _inherit = ["abstract.approval.type"]
    _order = 'sequence, id'
    sequence = fields.Integer()
    approval_task_id = fields.Integer(copy=False)
    approval_stage_id = fields.Integer(copy=False)
    approval_strategy_stage_id = fields.Many2one(
        'approval.strategy.config.stage',
        'Approval Stage ID',
        help="ID of the approval stage associated with this transaction",
        ondelete='cascade',
        copy=False
    )

    def create_tuple(self):
        """
          ``(0, 0, values)``
              adds a new record created from the provided ``value`` dict.
          ``(1, id, values)``
              updates an existing record of id ``id`` with the values in
              ``values``. Can not be used in :meth:`~.create`.
          ``(2, id, 0)``
              removes the record of id ``id`` from the set, then deletes it
              (from the database). Can not be used in :meth:`~.create`.
          ``(3, id, 0)``
              removes the record of id ``id`` from the set, but does not
              delete it. Can not be used in
              :meth:`~.create`.
        """
        data = self.copy_data()[0]
        approval_stage_id = data.pop('approval_stage_id', None)
        approval_task_id = data.pop('approval_task_id', None)
        if self.approval_task_id:
            return (1, self.approval_task_id, data)
        else:
            return (0, 0, data)


class ApprovalStrategyConfig(models.TransientModel):
    _name = "approval.strategy.config.stage"
    _inherit = "abstract.approval.stage"
    _description = """
    Helper for create new Approval Config Stage Wizard
    
    This model is used to configure the approval process
    """
    stage_mandatory = fields.Boolean()

    # stage_strategy_model_name = fields.Char()

    error_message = fields.Text(copy=False)
    approval_stage_id = fields.Integer(copy=False)
    approval_stage_model_name = fields.Char(copy=False)
    approval_tasks = fields.One2many(
        comodel_name='approval.strategy.config.task',
        inverse_name='approval_strategy_stage_id',
        string='Approval Tasks',
        help="Tasks of approval stages for the transaction.",
        copy=False
    )

    transaction_stage_field = fields.Char()

    @api.model
    def get_approval_strategy_config(self, transaction_object=None, **kwargs):
        return {}

    def get_all_approval_strategy_config(self, strategies=None, transaction_object=None):
        """
        Mengambil konfigurasi approval strategy untuk model tertentu.
        :param strategies: List nama strategy (tanpa prefix model)
        :param transaction_object: Record transaksi yang sedang diproses
        :return: Dict {transaction_stage_field: config_data}
        """
        strategies = strategies or []
        env = self.env

        result = {}

        for strategy_config_name in strategies:
            model_name = f"approval.strategy.config.stage.{strategy_config_name}"

            if model_name in env:
                config_model = env[model_name]
                if hasattr(config_model, "get_approval_strategy_config"):
                    config_data = config_model.get_approval_strategy_config(transaction_object=transaction_object)
                    if isinstance(config_data, dict) and "transaction_stage_field" in config_data:
                        result[config_data["transaction_stage_field"]] = config_data

        return result

    @api.model
    def default_get(self, fields):
        # loading data
        res = super().default_get(fields)
        # Ambil active node transaction id
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        approval_stage_id = res.get('approval_stage_id') or self.env.context.get('default_approval_stage_id')
        approval_stage_model_name = res.get('approval_stage_model_name') or self.env.context.get(
            'default_approval_stage_model_name') or 'approval.transaction.stage'

        if active_model == 'approval.transaction.stage' and active_id:
            record = self.env[active_model].browse(active_id)
        elif approval_stage_id:
            record = self.env[approval_stage_model_name].browse(approval_stage_id)
        else:
            record = None

        if record:
            """
            Update default wizard field from main record
            """
            approval_tasks = [(5, 0, 0)]
            approval_tasks.extend([(0, 0, {
                'sequence': task.sequence,
                'approval_task_id': task.id,
                'type_approval': task.type_approval,
                'user_id': task.user_id.id,
                'group_id': task.group_id.id,
            }) for task in record.approval_tasks])
            res.update({
                'approval_tasks': approval_tasks,
            })
        return res

    def button_create(self):
        context = self.env.context
        obj = self.env[context.get('active_model')].browse(context.get('active_id'))
        stage = self.copy_data()[0]
        transaction_stage_field = self.transaction_stage_field
        if self.approval_stage_id:
            # update dari stage wizard ke stage yang sudah ada
            old_approval_task_ids = self.env["approval.transaction.task"].search(
                [('approval_stage_id', '=', self.approval_stage_id)], order='id').ids
            old_stage = self.env["approval.transaction.stage"].browse(self.approval_stage_id)
            create_update_approval_task = [x.create_tuple() for x in self.approval_tasks]
            delete_approval_task_ids = set(old_approval_task_ids) - set(
                x.approval_task_id for x in self.approval_tasks if x.approval_task_id)
            create_update_approval_task.extend([(3, x, 0) for x in delete_approval_task_ids])
            stage['approval_tasks'] = create_update_approval_task
            old_stage.write(stage)
        else:
            # create stage baru
            stage['approval_tasks'] = [x.create_tuple() for x in self.approval_tasks]
            resul = self.env["approval.transaction.stage"].create([stage])
            if transaction_stage_field and hasattr(obj, transaction_stage_field):
                obj.write({
                    transaction_stage_field: resul.id
                })

        return {'type': 'ir.actions.act_window_close'}

    def button_reset_stage(self):
        pass

    def raise_error(self, source, message=None, error=None, view_id=None):
        _logger.error("Error creating new approval stage: %s", error)
        context = dict(self.env.context, default_error_message=message or str(error))
        context.update(
            [("default_" + k, v) for k, v in source.items()]
        )
        return ShowWizardFormError(
            action_form={
                'name': 'Create Stage',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': self._name,
                'view_id': view_id or self.env.ref('antareja_approval.view_approval_strategy_config_form').id,
                'target': 'new',
                'context': context,
            }
        )

    def edit_form(self, **kwargs):
        context = dict(self.env.context)
        context.update(
            ("default_" + k, v) for k, v in kwargs.items()
        )
        return {
            'name': 'Create Stage',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': self._name,
            'view_id': self.env.ref('antareja_approval.view_approval_strategy_config_form').id,
            'target': 'new',
            'context': context,
        }

    def create_new_stage(self, source=None, view_id=None, show_wizard_form_when_error=None):
        """Create a new approval stage for HR employee."""
        source = source or {}
        if 'transaction_stage_field' not in source:
            source['transaction_stage_field'] = self.env.context.get('transaction_stage_field', 'stage_inline_id')

        # Try Create a New stage

        try:
            ModelStage = self.env['approval.transaction.stage']
            _fields = dict(ModelStage._fields)
            approval_tasks = source.get('approval_tasks')
            if approval_tasks:
                # Convert approval_tasks to tuples for create
                source['approval_tasks'] = ensure_create_tuples_many2one(approval_tasks)
            elif source.get('stage_strategy_inline'):
                _logger.info("Next capture")
            else:
                raise UserError(_("Approval tasks are required to create a new stage."))
            # save only field that exist in approval.transaction.stage
            filter_source = {k: v for k, v in source.items() if k in _fields}
            return ModelStage.create([filter_source])[0]
        except ShowWizardFormError as swe:
            raise swe
        except Exception as e:
            if show_wizard_form_when_error:
                raise self.raise_error(source, message=str(e), view_id=view_id)
            else:
                _logger.error("Error creating new approval stage: %s", e)
                raise e

    # ########################################################
    # rule when stage running

    def validate_approval_before_approve(self, transaction_object, approval_stage_object):
        """
        Validate approval stages before approving.
        This method should be overridden by child models to provide specific
        approval validation logic.
        """
        # Example validation logic
        pass

    def execution_after_approved(self, transaction_object, approval_stage_object):
        """
        This method should be overridden by child models to provide specific logic
        """
        pass

    def execution_after_rejected(self, transaction_object, approval_stage_object):
        """
        This method should be overridden by child models to provide specific
        approval validation logic.
        """
        pass
