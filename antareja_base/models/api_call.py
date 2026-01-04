# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import json
import logging
from datetime import timedelta
from ..tools.utils import safe_call_method, have_method

_logger = logging.getLogger(__name__)


class AppCallReTryMixin(models.AbstractModel):
    _name = "api.call.retry.able.mixin"

    api_call_retry_ids = fields.Many2many('api.call.retry', compute='compute_api_call_retry_ids')
    api_call_need_retry = fields.Boolean(compute='compute_api_call_retry_ids')

    def compute_api_call_retry_ids(self):
        for rec in self:
            api_call_retry_ids = self.api_call_retry_ids.search(
                [('res_model', '=', self._name), ('res_id', '=', rec.id), ('state', '!=', 'done')])
            rec.api_call_retry_ids = api_call_retry_ids
            rec.api_call_need_retry = api_call_retry_ids

    def need_retry_method(self, res_method, error_message=None, param_args=None, param_kwargs=None, **kwargs):
        return self.env['api.call.retry'].need_retry(
            self._name, self.id, res_method,
            error_message=error_message, param_args=param_args, param_kwargs=param_kwargs
        )


class AppCallReTry(models.Model):
    _name = 'api.call.retry'

    state = fields.Selection([
        ('retry', 'Retry'),
        ('error', 'Error'),
        ('done', 'Done'),
    ], default='retry')

    res_id = fields.Integer()
    res_model = fields.Char()
    res_method = fields.Char()
    error_message = fields.Text()
    last_call = fields.Datetime(default=fields.Datetime.now)
    next_call = fields.Datetime(default=lambda self: fields.Datetime.now() + timedelta(hours=1))
    param_args = fields.Text()
    param_kwargs = fields.Text()

    def get_object(self):
        if not self.res_model:
            return False
        if not self.res_id:
            return self.env[self.res_model].browse()
        """Get the parent document ID if available."""
        # This method should be overridden in child classes if needed
        return self.env[self.res_model].browse(self.res_id)

    def mark_retry(self):
        self.write({'state': 'retry'})

    def retry(self):
        res = self.ensure_one()
        res.write({'state': 'done'})
        obj = res.get_object()
        if obj:
            param_args = json.loads(res.param_args) if res.param_args else []
            param_kwargs = json.loads(res.param_kwargs) if res.param_kwargs else {}
            safe_call_method(obj.with_context(__api_call_retry_id=res.id), res.res_method, *param_args, **param_kwargs)
        else:
            _logger.warning(f"API Call Retry: Object {res.res_model} with ID {res.res_id} not found.")
            return

    def need_retry(self, res_model, res_id, res_method, error_message=None, param_args=None, param_kwargs=None):
        if self:
            api_call_retry = self
        else:
            api_call_retry = self.search(
                [('res_model', '=', res_model), ('res_id', '=', res_id), ('res_method', '=', res_method)]
                , limit=1
            )
        last_call = fields.Datetime.now()
        update = {
            'last_call': last_call,
            'state': 'retry',
            'error_message': error_message
        }

        if param_args:
            update['param_args'] = json.dumps(param_args)
        else:
            update['param_args'] = False

        if param_kwargs:
            update['param_kwargs'] = json.dumps(param_kwargs)
        else:
            update['param_kwargs'] = False

        next_call = last_call + timedelta(hours=2)

        if api_call_retry:
            api_call_retry.last_call = last_call

            if api_call_retry.last_call > next_call:
                update['next_call'] = next_call
            api_call_retry.write(update)
        else:
            update.update({
                'res_model': res_model,
                'res_id': res_id,
                'res_method': res_method,
                'next_call': next_call,
            })
            api_call_retry = self.create([update])[0]
        self.env['api.call.log'].create({
            'api_call_retry_id': api_call_retry.id,
            'error_message': error_message
        })
        return api_call_retry


class AppCallLog(models.Model):
    _name = 'api.call.log'

    api_call_retry_id = fields.Many2one('api.call.retry')
    call_datetime = fields.Datetime(default=fields.Datetime.now)
    error_message = fields.Text()
