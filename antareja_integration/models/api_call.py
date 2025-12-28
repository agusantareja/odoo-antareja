# -*- coding: utf-8 -*-

import requests
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import traceback
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class AppCallReTry(models.Model):
    _inherit = 'api.call.retry'

    # state = fields.Selection([
    #     ('retry', 'Retry'),
    #     ('error', 'Error'),
    #     ('done', 'Done'),
    # ], default='retry')
    #
    # res_id = fields.Integer()
    # res_model = fields.Char()
    # res_method= fields.Char()
    # error_message = fields.Text()
    # last_call = fields.Datetime(default=fields.Datetime.now)
    # next_call = fields.Datetime()
    #
    # def get_object(self):
    #     if not self.res_model:
    #         return False
    #     if not self.res_id:
    #         return self.env[self.res_model].browse()
    #     """Get the parent document ID if available."""
    #     # This method should be overridden in child classes if needed
    #     return self.env[self.res_model].browse(self.res_id)
    #
    # def mark_retry(self):
    #     self.write({'state':'retry'})

    def cron_retry(self):
        records = self.search([('state', '=', 'retry')], order='next_call', limit=1000)
        for rec in records:
            rec.retry()
