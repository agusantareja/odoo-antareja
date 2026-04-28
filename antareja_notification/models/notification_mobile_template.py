# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models
from odoo.addons.antareja_base.tools.utils import safe_call_method, have_method
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr

_logger = logging.getLogger(__name__)


class NotificationMobileTemplate(models.Model):
    _name = "notification.mobile.template"
    _description = "Notification Mobile Template"

    active = fields.Boolean(default=True)
    name = fields.Char("Notification")
    model_id = fields.Many2one('ir.model')
    model = fields.Char("Model",related="model_id.model")
    DEFAULT_PYTHON_CODE = """# Available variables:
            #  - env: Odoo Environment on which the action is triggered
            #  - notification
            #  - data : data part notification firebase
            # To return an response, assign: response = {...}

            \n\n\n\n
            """
    title = fields.Char()
    body = fields.Char()
    image = fields.Char()

    code = fields.Text(
        string='Python Code',
        default=DEFAULT_PYTHON_CODE,
        help="Write Python code that the action will execute. Some variables are "
             "available for use; help about python expression is given in the help tab."
    )

    def get_application_name(self):
        return self.env['ir.config_parameter'].get_param('antareja.application_name')

    def send_notification_to_users(self, users, res_id,**kwargs):
        for notification_to_user in users:
            self.with_context(notification_to_user=notification_to_user).send(notification_to_user, res_id)

    def send_notification_to_user(self, notification_to_user, res_id,**kwargs):
        Template = self.env['mail.template']
        template = self.ensure_one()
        fields = ['title','body','image']
        notification = {}
        for field in fields:
            Template = Template.with_context(safe=field in {'title'})
            notification[field] = Template._render_template(getattr(template, field), template.model, res_id)
        data ={
            'source_application': self.get_application_name(),
            'source_model': self.model,
            'source_res_id' : res_id,
            'notification_to_user': notification_to_user.partner_id.email,
        }
        approval_task_line = kwargs.get('approval_task_line')
        if approval_task_line:
            data.update(
                source_approval_model=approval_task_line._name,
                source_approval_res_id=approval_task_line.id
            )
        eval_context = self._get_eval_context()
        transaction_object = self.env[self.model].sudo().browse(res_id)
        eval_context['object'] = eval_context['record'] = transaction_object
        eval_context['notification'] = notification

        eval_context['data']=data
        eval_context = self._run_action_code_multi(eval_context)
        data = eval_context.get('data')
        if 'url' not in data and not data.get('url'):
            data['source_url'] = safe_call_method(transaction_object,'get_internal_url') or None
        payload = {
            'notification': eval_context.get('notification'),
            'data':data
        }
        return self.send_notification(payload)

    @api.model
    def send_notification(self,payload):
        _logger.error("implemntation not found")
        pass
    # notification.mobile.target (internal,remote,firebase)

    @api.model
    def _get_eval_context(self):
        """ evaluation context to pass to safe_eval """

        return {
            'env': self.env,
            'uid': self._uid,
            'user': self.env.user,
        }

    @api.constrains('code')
    def _check_python_code(self):
        for action in self.sudo().filtered('code'):
            msg = test_python_expr(expr=action.code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def _run_action_code_multi(self, eval_context):
        safe_eval(self.code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'action'
        return eval_context
