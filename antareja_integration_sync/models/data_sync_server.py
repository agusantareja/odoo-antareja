# -*- coding: utf-8 -*-

import requests
from odoo import models, fields, _
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

    application_server_auth_id = fields.Many2one('application.server.auth', string="Application Server Auth")
    application_server_path_id = fields.Many2one('application.server.path', string="Application Server Path")

    def get_sync_path(self):
        return "/api/sync/data"

    def get_db_name_uid_password(self):
        rec = self.ensure_one()
        if rec.external_mode == 'server_auth':
            db, uid, password = rec.application_server_auth_id.jsonrpc_authenticate()
            return db, uid, password

        if rec.external_mode == 'server_path':
            db, uid, password = rec.application_server_path_id.application_server_auth_id.jsonrpc_authenticate()
            return db, uid, password

        return super(ExternalServerSync, self).get_db_name_uid_password()

    def jsonrpc_call(self, model, method, args, kw=None, db=None, uid=None, password=None):
        rec = self.ensure_one()
        if rec.external_mode == 'server_auth':
            return rec.application_server_auth_id.jsonrpc_call(
                model, method, args, kw=kw, db=db, uid=uid, password=password
            )

        if rec.external_mode == 'server_path':
            return rec.application_server_path_id.application_server_auth_id.jsonrpc_call(
                model, method, args, kw=kw, db=db, uid=uid, password=password
            )

        return super(ExternalServerSync, self).jsonrpc_call(
            model, method, args, kw=kw, db=db, uid=uid, password=password
        )

    def get_external_data(self, model_name, domain=None, fields=None, offset=None, limit=None, count=False,
                          object_id=None, context=None):
        rec = self.ensure_one()
        if rec.external_mode == 'server_auth':
            return rec.application_server_auth_id.get_external_data(
                model_name, domain=domain, fields=fields, offset=offset,
                limit=limit, count=count, object_id=object_id,
                context=context,  path=rec.get_sync_path()
            )

        if rec.external_mode == 'server_path':
            return rec.application_server_path_id.application_server_auth_id.get_external_data(
                model_name, domain=domain, fields=fields, offset=offset,
                limit=limit, count=count, object_id=object_id,
                context=context
            )

        return super(ExternalServerSync, self).get_external_data(
            model_name, domain=domain, fields=fields, offset=offset, limit=limit,
            count=count, object_id=object_id, context=context
        )
