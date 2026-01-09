# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import json
import logging
from datetime import timedelta
from ..tools.utils import safe_call_method, have_method

_logger = logging.getLogger(__name__)


class AppCallReTry(models.Model):
    _name = 'antareja.delay.call'

    state = fields.Selection([
        ('prepare', 'Prepare'),
        ('retry', 'Retry'),
        ('process', 'Process'),
        ('error', 'Error'),
        ('done', 'Done'),
    ], default='prepare')
    user_id = fields.Many2one(
        'res.users',
        'User Executor'
    )
    company_id = fields.Many2one(
        'res.company'
    )
    res_model = fields.Char()
    res_method = fields.Char()
    param_json = fields.Text()
    error_message = fields.Text()
    last_call = fields.Datetime(default=fields.Datetime.now)
    next_call = fields.Datetime(default=lambda self: fields.Datetime.now() + timedelta(hours=1))

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

    def execute_delay(self):
        res = self.ensure_one()
        res.write({'state': 'done'})
        param_json = json.loads(res.param_json)
        record = self.env[self.res_model]
        if res.user_id:
            record = record.with_user(res.user_id)
        if res.company_id:
            record = record.with_user(res.company_id)

        record = record.with_context(__api_call_delay_id=res.id)
        param_args = json.loads(res.param_args) if res.param_args else []
        param_kwargs = json.loads(res.param_kwargs) if res.param_kwargs else {}

        return safe_call_method(record, res.res_method, param_args, param_kwargs)


    def need_delay(
            self, record, res_method,delay_in_second=None, param_args=None, param_kwargs=None,param_context=None
    ):
        res_model = record._name
        param_json = {
            'ids': record.ids or [],
            'param_args': param_args or [],
            'param_kwargs': param_kwargs or {},
            'param_context': param_context or {},
        }
        next_call = fields.Datetime.now() + timedelta(seconds=delay_in_second or 10)
        param_json['ids']= record.ids or []

        update = {
            'res_model':res_model,
            'res_method':res_method,
            'next_call': next_call,
        }
        api_call_delay = self.create([update])[0]
        return api_call_delay


# class AppCallLog(models.Model):
#     _name = 'api.call.log'
#
#     api_call_retry_id = fields.Many2one('api.call.retry')
#     call_datetime = fields.Datetime(default=fields.Datetime.now)
#     error_message = fields.Text()
