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

    def cron_retry(self):
        records = self.search([('state', '=', 'retry')], order='next_call', limit=1000)
        for rec in records:
            rec.retry()
