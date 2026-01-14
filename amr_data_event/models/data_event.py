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
    _name = 'internal.data.event'
    _description = "Internal data event yang akan assess oleh appliance external"

    res_model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True, index=True)
    event_datetime = fields.Datetime()
    operation = fields.Selection([
        ('create', 'Create'),
        ('write', 'Write'),
        ('unlink', 'Delete'),
    ], required=True)

    changed_fields = fields.Char()

    state = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ], default='pending', index=True)

    error_message = fields.Text()
