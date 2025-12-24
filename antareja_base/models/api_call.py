# -*- coding: utf-8 -*-

import requests
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import traceback
import logging
from datetime import datetime, timedelta

from ..tools.utils import save_call_method

_logger = logging.getLogger(__name__)

class AppCallReTryMixin(models.AbstractModel):
    _name = "api.call.retry.able.mixin"

    api_call_retry_ids= fields.Many2many('api.call.retry',compute='compute_api_call_retry_ids')
    api_call_need_retry= fields.Boolean(compute='compute_api_call_retry_ids')

    def compute_api_call_retry_ids(self):
        for rec in self:
            api_call_retry_ids = self.api_call_retry_ids.search(
                [('res_model', '=', self._name), ('res_id', '=', rec.id), ('state', '!=', 'done')])
            rec.api_call_retry_ids = api_call_retry_ids
            rec.api_call_need_retry = api_call_retry_ids

    def need_retry_method(self,res_method,error_message=None,**kwargs):
        return self.env['api.call.retry'].need_retry(self._name, self.id, res_method, error_message=error_message)

class AppCallReTry(models.Model):
    _name = 'api.call.retry'

    state = fields.Selection([
        ('retry', 'Retry'),
        ('error', 'Error'),
        ('done', 'Done'),
    ], default='retry')

    res_id = fields.Integer()
    res_model = fields.Char()
    res_method= fields.Char()
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
        self.write({'state':'retry'})

    def retry(self):
        res = self.ensure_one()
        res.write({'state':'done'})
        obj = res.get_object()
        save_call_method(obj,res.res_method)

    def need_retry(self,res_model,res_id,res_method,error_message=None):
        api_call_retry = self.search([('res_model','=',res_model),('res_id','=',res_id),('res_method','=',res_method)],limit=1)
        last_call = fields.Datetime.now()
        update = {
            'last_call': last_call,
            'state': 'retry',
            'error_message':error_message
        }
        next_call = last_call + timedelta(hours=2)
        if api_call_retry:
            api_call_retry.last_call=last_call

            if api_call_retry.last_call > next_call :
                update['next_call'] = next_call
            api_call_retry.write(update)
        else:
            update.update({
                'res_model':res_model,
                'res_id':res_id,
                'res_method':res_method,
                'next_call': next_call,
            })
            api_call_retry=self.create([update])[0]
        self.env['api.call.log'].create({
            'api_call_retry_id':api_call_retry.id,
            'error_message':error_message
        })
        return api_call_retry




class AppCallLog(models.Model):
    _name = 'api.call.log'

    api_call_retry_id = fields.Many2one('api.call.retry')
    call_datetime = fields.Datetime(default=fields.Datetime.now)
    error_message= fields.Text()
