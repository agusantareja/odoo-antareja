# -*- coding: utf-8 -*-

import ast
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import json
import traceback
import logging

_logger = logging.getLogger(__name__)


class InternalDataSync(models.Model):
    _name = 'external.data.event'
    _description = "Internal data event yang akan assess oleh external app"
    _order = 'id desc'

    server_id = fields.Many2one('external.server.sync')
    strategy_ids = fields.Many2many('external.data.sync.strategy')
    data_ids = fields.Many2many('external.data.sync')
    external_odoo_id  = fields.Integer('Id External')

    name = fields.Char()
    res_model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True, index=True)
    event_datetime = fields.Datetime(default=fields.Datetime.now)
    operation = fields.Selection([
        ('create', 'Create'),
        ('write', 'Write'),
        ('unlink', 'Delete'),
    ], required=True)
    changed_fields = fields.Char()
    state = fields.Selection([
        ('pending', 'Pending'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], default='pending', index=True)
    error_message = fields.Text()

