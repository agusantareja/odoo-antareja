# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.safe_eval import safe_eval, test_python_expr
from pytz import timezone
from ..tools.utils import safe_call_method

import base64
import logging

_logger = logging.getLogger(__name__)


class ApprovalTemplateMixin(models.AbstractModel):
    _name = 'approval.template.mixin'
    DEFAULT_PYTHON_CODE = """# Available variables:
        #  - env: Odoo Environment on which the action is triggered
        #  - time, datetime, dateutil, timezone: useful Python libraries
        #  - float_compare: Odoo function to compare floats based on specific precisions
        #  - log: log(message, level='info'): logging function to record debug information in ir.logging table
        #  - UserError: Warning Exception to use with raise
        #  - Command: x2Many commands namespace
        #  - approval_instance
        #  - approval_template
        # To return an response, assign: response = {...}

        \n\n\n\n
        """

    model_id = fields.Many2one('ir.model')
    model = fields.Char(related='model_id.model', store=True)

    # approval.task.line.mixin
    approval_task_line_model_id = fields.Many2one('ir.model')
    approval_task_line_model = fields.Char(related='approval_task_line_model_id.model', store=True)

    view_name = fields.Char()

    state_field = fields.Char()
    state_reject = fields.Char(help="State when reject")
    state_approved = fields.Char(help="State when approved. Leve blank when not need update")
    state_waiting_approvals = fields.Char(help="Waiting Approval for approval_line")

    invoke_validate_request_approval = fields.Char()
    invoke_approval_start = fields.Char()
    invoke_approval_done = fields.Char()
    invoke_before_approve = fields.Char()
    invoke_after_approve = fields.Char()
    invoke_before_reject = fields.Char()
    invoke_after_reject = fields.Char()

    notes_chatter_approved = fields.Boolean("Note Chatter Approve")
    notes_chatter_rejected = fields.Boolean("Note Chatter Rejected")

    code = fields.Text(
        string='Python Code',
        default=DEFAULT_PYTHON_CODE,
        help="Write Python code that the action will execute. Some variables are "
             "available for use; help about python expression is given in the help tab."
    )

    def invoke_method(self, transaction_object, method_name,kwargs=None):
        atts_method_name = f"invoke_{method_name}"
        object_method_name = getattr(self, atts_method_name)
        safe_call_method(transaction_object, object_method_name, kwargs=kwargs)

    def get_state_waiting_approvals(self):
        if self.state_waiting_approvals:
            return self.state_waiting_approvals.split(',')
        else:
            return ['waiting_approval']

    def get_state_field(self):
        state_field = 'state'
        if not self:
            return state_field
        return self.state_field or state_field

    def get_state_reject(self):
        return self and self.state_reject

    def get_state_approved(self):
        return self and self.state_approved

    def prepare_dict(self):
        return {'model_id': self.model_id.id}

    def get_transaction_status(self, transaction):
        rec = self.ensure_one()
        state_field = rec.get_state_field()
        return transaction and getattr(transaction, state_field)

    def is_status_waiting_approval(self, transaction):
        rec = self.ensure_one()
        state_field = rec.get_state_field()
        state_waiting_approvals = rec.get_state_waiting_approvals()
        return transaction and getattr(transaction, state_field) in state_waiting_approvals

    @api.model
    def _get_eval_context(self, approval_instance):
        """ evaluation context to pass to safe_eval """
        transaction_object = approval_instance and approval_instance.get_transaction_object()
        response = {
            'approval_instance': approval_instance,
            'transaction_object': transaction_object,
            'approval_template': self,
        }
        return {
            'env': self.env,
            'uid': self._uid,
            'user': self.env.user,
            # 'time': tools.safe_eval.time,
            # 'datetime': tools.safe_eval.datetime,
            # 'dateutil': tools.safe_eval.dateutil,
            'timezone': timezone,
            'float_compare': float_compare,
            'b64encode': base64.b64encode,
            'b64decode': base64.b64decode,
            'approval_instance': approval_instance,
            'approval_template': self,
            'transaction_object': transaction_object,
            'response': response
        }

    @api.constrains('code')
    def _check_python_code(self):
        for action in self.sudo().filtered('code'):
            msg = test_python_expr(expr=action.code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def _run_action_code_multi(self, eval_context):
        safe_eval(self.code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'action'
        return eval_context.get('response')

    # Configurasi tambahan
    def get_config_instance(self, approval_instance):
        return self._run_action_code_multi(self._get_eval_context(approval_instance))

    def search_template(self, transaction=None, transaction_model_name=None):
        if transaction:
            transaction_model_name = transaction._name

        if not transaction_model_name:
            raise UserError("Model Name not set")

        return self.search([('model_id.model', '=', transaction_model_name)], limit=1)

    @api.model
    def get_notification_approval(self):
        return None

    @api.model
    def get_notification_rejection(self):
        return None

    @api.model
    def get_notification_approved(self):
        return None


class ApprovalTemplate(models.Model):
    _name = 'approval.template'
    _inherit = ['approval.template.mixin']
    _description = """Template configurasi dari appporval tempalate agar lebih mudah untuk di register/unregister approval.task"""

    _sql_constraints = [
        ('model_id_unique', 'unique(model_id)', 'Model must be uniq!')
    ]
#
