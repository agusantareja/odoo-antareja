# -*- coding: utf-8 -*-

from odoo import models, fields

import logging

_logger = logging.getLogger(__name__)


class InternalDataSync(models.Model):
    _name = 'internal.data.event.config'
    _description = """
    """

    model_id = fields.Many2one(
        'ir.model',
        required=True,
        ondelete='cascade'
    )
    field_monitor = fields.Char()
    log_create = fields.Boolean(default=True)
    log_write = fields.Boolean(default=True)
    log_unlink = fields.Boolean(default=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('uniq_model', 'unique(model_id)', 'Audit config already exists')
    ]

    def get_fields_monitor(self):
        return set(self.field_monitor and [x.trim() for x in self.field_monitor.split(',')])

    def get_config_create(self, model_name):
        return self.search([
            ('model_id.model', '=', model_name),
            ('active', '=', True),
            ('log_create', '=', True),
        ], limit=1) and True

    def get_config_write(self, model_name):
        return self.search([
            ('model_id.model', '=', model_name),
            ('active', '=', True),
            ('log_write', '=', True),
        ], limit=1) and True

    def get_config_unlink(self, model_name):
        return self.search([
            ('model_id.model', '=', model_name),
            ('active', '=', True),
            ('log_unlink', '=', True),
        ], limit=1) and True
