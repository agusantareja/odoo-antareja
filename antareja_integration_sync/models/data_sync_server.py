# -*- coding: utf-8 -*-

import requests
from odoo import models, fields,api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ExternalServerSync(models.Model):
    _inherit = 'external.server.sync'
    app_name = fields.Char(
        compute='_compute_external_app_name',
        inverse='_inverse_external_app_name',
        store=True)
    external_mode = fields.Selection([
        ('standard', 'Standard API'),
        ('server_auth', 'Server Authentication '),
        ('server_path', 'Server Path '),
    ], default='standard')

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
                rec.app_name = rec.application_server_auth_id.get_application_name()
            # kalau server_sync_id kosong → JANGAN override
            # biarkan nilai manual tetap

    # ===== INVERSE =====
    def _inverse_external_app_name(self):
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

    # ===== INVERSE =====
    def _inverse_server_auth(self):
        for rec in self:
            # inverse wajib ada supaya field editable
            pass

    @api.model
    def get_sync_path(self):
        return "/api/sync/data"

    def get_application_server_auth(self):
        if self.external_mode == 'server_auth':
            return self.application_server_auth_id.application_server_id
        elif self.external_mode == 'server_path':
            return self.application_server_path_id.application_server_auth_id.application_server_id

    def get_application_name(self):
        auth = self.get_application_server_auth()
        return (auth and auth.get_application_name()) or super(ExternalServerSync, self).get_application_name()


    def get_endpoint_url(self):
        auth = self.get_application_server_auth()
        return (auth and auth.get_endpoint_url()) or super(ExternalServerSync, self).get_endpoint_url()
    #
    # def get_external_data(self, model_name, domain=None, fields=None, offset=None, limit=None, count=False,
    #                       object_id=None, context=None):
    #     rec = self.ensure_one()
    #     if not self.get_application_name():
    #         raise UserError(_("Application Server is not set for External Server Sync '%s'") % rec.name)
    #
    #     if rec.external_mode == 'server_auth':
    #         return rec.application_server_auth_id.get_external_data(
    #             model_name, domain=domain, fields=fields, offset=offset,
    #             limit=limit, count=count, object_id=object_id,
    #             context=context, path=rec.get_sync_path()
    #         )
    #
    #     if rec.external_mode == 'server_path':
    #         return rec.application_server_path_id.application_server_auth_id.get_external_data(
    #             model_name, domain=domain, fields=fields, offset=offset,
    #             limit=limit, count=count, object_id=object_id,
    #             context=context
    #         )
    #
    #     return super(ExternalServerSync, self).get_external_data(
    #         model_name, domain=domain, fields=fields, offset=offset, limit=limit,
    #         count=count, object_id=object_id, context=context
    #     )

    def get_auth_config(self):
        config = super(ExternalServerSync, self).get_auth_config()
        auth = self.get_application_server_auth()
        if auth:
            config = auth.get_auth_config(config)
        return config

    def get_odoo_client(self, **kwargs):
        auth = self.get_application_server_auth()
        if auth:
            return auth.create_auth_client(**kwargs)
        else:
            return super(ExternalServerSync, self).create_auth_client(**kwargs)