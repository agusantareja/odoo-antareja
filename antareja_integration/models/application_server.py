# -*- coding: utf-8 -*-

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ApplicationServer(models.Model):
    _inherit = 'application.server'

    application_server_auth_ids = fields.One2many(
        'application.server.auth', 'application_server_id'
    )
    application_server_path_ids = fields.One2many(
        'application.server.path', 'application_server_id',
        readonly=True
    )
