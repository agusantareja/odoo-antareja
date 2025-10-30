from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
import logging
import re
from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError

_logger = logging.getLogger(__name__)
SNAKE_CASE_REGEX = re.compile(r'^[a-z_][a-z0-9_]*$')


class ApprovalStrategyTemplateInstance(models.Model):
    _name = "approval.strategy.template.instance"
    _inherit = 'abstract.approval.instance'
    _description = """ """

    active = fields.Boolean(
        default=True,
        string="Active"
    )
    sequence = fields.Integer(
        default=10, string='Sequence',
        help="Sequence of the approval strategy template instance."
    )
    name = fields.Char()
    code = fields.Text(string="Get template stage from python code", required=True)
    approval_template_stage_ids = fields.One2many(
        comodel_name='approval.strategy.template.stage',
        inverse_name='approval_template_instance_id',
        string='Approval Template Stages',
        help="Stages of the approval strategy template."
    )

    def get_approval_instance_config(self, **kwargs):
        self.ensure_one()

        try:
            target_model = self.env[self.transaction_model_name]
            # config_model = self.env[self.stage_strategy_config_model_name]
        except Exception:
            raise ValueError(_("Invalid model name: %s") % self.transaction_model_name)
        field_names = self._fields.keys()
        config_self = {}
        for field_name in field_names:
            field_type = self._fields[field_name].type
            if field_type in ('one2many', 'many2many'):
                continue
            value = self[field_name]
            if field_type != 'many2one':
                config_self[field_name] = value
            elif value:
                config_self[field_name] = value.id
        config_self.update({
            'transaction_model_name': self.transaction_model_name,
        })

        kwargs = dict(kwargs or {})
        config = dict(kwargs.get('config', {}))
        config.update(config_self)
        kwargs.update(config_self)
        kwargs['config'] = config

        local_dict = {
            'env': self.env,
            'model': target_model,
            'kwargs': kwargs,
            'self': target_model,
            'result': None,
        }

        try:
            safe_eval(self.code.strip(), local_dict, mode='exec', nocopy=True)
            return local_dict.get('result')
        except Exception as e:
            _logger.exception("Error executing approval strategy script: %s", e)
            raise ValueError(_("Execution Error:\n%s") % str(e))

    def create_approval_instance(self, transaction_object, **kwargs):
        """
        Create an approval instance based on the provided transaction object and configuration.
        :param transaction_object: Record of the transaction model.
        :param kwargs: Additional keyword arguments for configuration.
        :return: Created approval instance record.
        """
        if not transaction_object or not isinstance(transaction_object, models.BaseModel):
            raise UserError(_("Invalid transaction object provided."))

        if self:
            approval_instance = self.ensure_one()
            if approval_instance.transaction_model_name != transaction_object._name:
                raise UserError(_("Transaction model name does not match the approval strategy template instance."))
        else:
            approval_instance = self.get_approval_strategy_template_instance(transaction_object)

        if not approval_instance:
            raise UserError(
                _("Approval strategy template instance not found for model: %s") % transaction_object.transaction_model_name)

        ModelInstance = self.env['approval.transaction.instance']
        _fields = dict(ModelInstance._fields)
        source = approval_instance.get_approval_instance_config(
            transaction_object=transaction_object,
        )
        # save only field that exist in approval.transaction.instance
        filter_source = {k: v for k, v in source.items() if k in _fields}

        filter_source['approval_template_instance_id'] = self.id
        filter_source['transaction_id'] = transaction_object.id
        filter_source['name'] = transaction_object.name
        if 'company_id' not in filter_source and  transaction_object and 'company_id' in transaction_object._fields:
            filter_source['company_id'] = transaction_object.company_id.id
        filter_source.pop('id')
        return ModelInstance.create([filter_source])[0]

    def get_approval_strategy_config(self, transaction_object=None,transaction_stage_field=None, stage_status=None,**kwargs):
        result = {}
        for rec in self.approval_template_stage_ids:
            if transaction_stage_field and rec.transaction_stage_field != transaction_stage_field:
                continue

            if stage_status and rec.status_waiting_approval != stage_status:
                continue

            config = rec.get_approval_strategy_config(transaction_object=transaction_object)
            if config:
                result[config["transaction_stage_field"]] = config

        return result

    def get_approval_strategy_template_instance(self, transaction_object=None, **kwargs):
        if not transaction_object or not isinstance(transaction_object, models.BaseModel):
            raise UserError(_("Invalid transaction object provided."))
        return self.search(
                [('transaction_model_name', '=', transaction_object._name)],
                limit=1
        )

    approval_stages = fields.One2many(store=False)

class ApprovalStrategyTemplateStage(models.Model):
    _name = "approval.strategy.template.stage"
    _inherit = 'abstract.approval.strategy.config'
    _description = """
    Approval Strategy Template Stage
    Build Stage 
    """
    _order = 'transaction_model_name, sequence, id'

    active = fields.Boolean(default=True)
    code = fields.Text(string="Get template stage from python code", required=True)
    result_output = fields.Text("Result", readonly=True)
    approval_template_instance_id = fields.Many2one(
        'approval.strategy.template.instance',
        string="Approval Template Instance",
        # required=True,
        # ondelete='cascade',
    )
    transaction_model_name = fields.Char(related='approval_template_instance_id.transaction_model_name',store=True,readonly=True )

    def name_get(self):
        return [
            (rec.id, f"[{rec.transaction_model_name}]({rec.stage_strategy_name}).{rec.transaction_stage_field or '-'}")
            for rec in self
        ]

    def get_approval_strategy_config(self, **kwargs):
        self.ensure_one()

        try:
            target_model = self.env[self.transaction_model_name]
            config_model = self.env[self.stage_strategy_config_model_name]
        except Exception:
            raise ValueError(_("Invalid model name: %s") % self.transaction_model_name)
        field_names = self.env['abstract.approval.strategy.config']._fields.keys()
        config_self = {}
        for field_name in field_names:
            field_type = self._fields[field_name].type
            if field_type in ('one2many', 'many2many'):
                continue
            value = self[field_name]
            if field_type != 'many2one':
                config_self[field_name] = value
            elif value:
                config_self[field_name] = value.id
        config_self.update({
            'transaction_model_name': self.transaction_model_name,
            'transaction_stage_field': self.transaction_stage_field,
            'stage_strategy_config_name': self.stage_strategy_config_name,
            'stage_strategy_config_model_name': self.stage_strategy_config_model_name,
        })

        kwargs = dict(kwargs or {})
        config = dict(kwargs.get('config', {}))
        config.update(config_self)
        kwargs.update(config_self)
        kwargs['config'] = config

        local_dict = {
            'env': self.env,
            'model': target_model,
            'config_model': config_model,
            'kwargs': kwargs,
            'self': target_model,
            'result': None,
        }

        try:
            safe_eval(self.code.strip(), local_dict, mode='exec', nocopy=True)
            return local_dict.get('result')
        except Exception as e:
            _logger.exception("Error executing approval strategy script: %s", e)
            raise ValueError(_("Execution Error:\n%s") % str(e))

    def action_try_config(self):
        for rec in self:
            result_str = rec.get_approval_strategy_config()
            rec.result_output = result_str

    def get_all_approval_strategy_config(self, strategies=None, transaction_object=None):
        """
        Mengambil konfigurasi approval strategy untuk model tertentu.
        :param strategies: List nama strategy (tanpa prefix model)
        :param transaction_object: Record transaksi yang sedang diproses
        :return: Dict {transaction_stage_field: config_data}
        """
        strategies = strategies or []

        result = {}
        domain = [('transaction_model_name', '=', transaction_object._name)]
        if strategies:
            domain.append(('stage_strategy_config_name', 'in', strategies))
        config_templates = self.search(domain)

        for config_template in config_templates:
            config_data = config_template.get_approval_strategy_config(transaction_object=transaction_object)
            result[config_data["transaction_stage_field"]] = config_data

        return result
