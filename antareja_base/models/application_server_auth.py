# -*- coding: utf-8 -*-

from requests import RequestException
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import requests
import logging

_logger = logging.getLogger(__name__)


class ApplicationServerAuthRestToken(models.AbstractModel):
    _name = 'application.server.auth.rest.token.mixin'

    # rest-token
    rest_token_in = fields.Selection([
        ('basic', 'Basic'),
        ('bearer', 'Bearer'),
        ('header', 'Header'),
        ('param', 'Parameter'),
        ('body', 'Body')
    ], default='header')
    rest_token_key = fields.Char(
        default='basic'
    )
    rest_token = fields.Char()
    rest_refresh = fields.Char()

class ApplicationServerAuthOdooRCP(models.AbstractModel):
    _name = 'application.server.auth.odoo.rcp.mixin'
    _inherit = 'application.server.auth.rest.token.mixin'
    # odoo rcp
    odoo_server_db = fields.Char()
    odoo_server_uid = fields.Integer()
    odoo_username = fields.Char()
    odoo_password = fields.Char()


class ApplicationServerAuth(models.Model):
    _name = 'application.server.auth'
    _inherit = ['application.server.auth.odoo.rcp.mixin',
                'ir.config_parameter.able.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char()
    application_server_id = fields.Many2one(
        'application.server'
    )
    application_server_path_ids = fields.One2many(
        'application.server.path',
        'application_server_auth_id'
    )
    auth_type = fields.Selection([
        ('odoo-rcp', 'Odoo RCP'),
        ('rest-token', 'Rest Token'),
    ], default='rest-token')

    username = fields.Char()
    password = fields.Char()

    def get_rest_token(self):
        return self.get_value_config_param(value_without_config_param=self.rest_token)

    def action_open_view(self):
        self.ensure_one()
        context = dict(self.env.context, default_application_server_id=self.id)
        return {
            'name': _('Server Auth'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'context': context
        }
