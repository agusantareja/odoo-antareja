# -*- coding: utf-8 -*-

import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ExternalServerSync(models.Model):
    _inherit = 'external.server.sync'

    external_mode = fields.Selection([
        ('standard', 'Standard API'),
        ('server_auth', 'Server Authentication '),
        ('server_path', 'Server Path '),
    ], default='standard')
    app_name = fields.Char(
        compute='_compute_external_app_name',
        inverse='_inverse_external_app_name',
        store=True
    )
    odoo_server_db = fields.Char(
        compute='_compute_external_app_name',
        inverse='_inverse_odoo_server_db',
        store=True
    )
    base_url = fields.Char(
        compute='_compute_external_app_name',
        inverse='_inverse_base_url',
        store=True
    )
    application_server_id = fields.Many2one(
        'application.server',
        compute = '_compute_external_app_name',
        readonly=True,
        store = True
    )
    application_server_auth_id = fields.Many2one(
        'application.server.auth',
        compute='_compute_server_auth',
        inverse='_inverse_server_auth',
        store=True,
        string="Application Server Auth"

    )
    application_server_path_id = fields.Many2one(
        'application.server.path',
        string="Application Server Path"
    )

    @api.depends('external_mode', 'application_server_auth_id', 'application_server_auth_id.name')
    def _compute_external_app_name(self):
        for rec in self:
            if rec.application_server_auth_id:
                rec.application_server_id = rec.application_server_auth_id.application_server_id
                rec.app_name = rec.application_server_auth_id.get_application_name()
                rec.base_url = rec.application_server_auth_id.get_endpoint_url()
                rec.odoo_server_db = rec.application_server_auth_id.odoo_server_db
            # kalau server_sync_id kosong → JANGAN override
            # biarkan nilai manual tetap

    # ===== INVERSE =====
    def _inverse_odoo_server_db(self):
        for rec in self:
            # inverse wajib ada supaya field editable
            pass

    def _inverse_external_app_name(self):
        for rec in self:
            # inverse wajib ada supaya field editable
            pass

    def _inverse_external_app_name(self):
        for rec in self:
            # inverse wajib ada supaya field editable
            pass

    def _inverse_base_url(self):
        for rec in self:
            # inverse wajib ada supaya field editable
            pass

    def _inverse_server_auth(self):
        for rec in self:
            # inverse wajib ada supaya field editable
            pass

    @api.depends('external_mode', 'application_server_path_id')
    def _compute_server_auth(self):
        for rec in self:
            if rec.external_mode == 'server_path' and rec.application_server_path_id:
                rec.application_server_auth_id = rec.application_server_path_id.application_server_auth_id
            # kalau server_sync_id kosong → JANGAN override
            # biarkan nilai manual tetap


    @api.model
    def get_sync_path(self):
        return "/api/sync/data"

    def get_application_server_auth(self):
        if self.external_mode == 'server_auth':
            return self.application_server_auth_id
        elif self.external_mode == 'server_path':
            return self.application_server_path_id.application_server_auth_id

    def create_remote_model(self,external_model, **kwargs):
        auth = self.get_application_server_auth()
        if auth:
            return auth.create_remote_model(external_model,**kwargs)
        else:
            return super(ExternalServerSync, self).create_remote_model(external_model,**kwargs)
