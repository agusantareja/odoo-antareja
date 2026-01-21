# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class AppCallReTry(models.Model):
    _inherit = 'api.call.retry'

    def cron_retry(self):
        records = self.search([('state', '=', 'retry')], order='next_call', limit=1000)
        for rec in records:
            rec.retry()
