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

    def get_application_name(self):
        if self.external_mode == 'server_auth':
            return self.application_server_auth_id.get_application_name()
        if self.external_mode == 'server_path':
            return self.application_server_path_id.get_application_name()
        return super(ExternalServerSync, self).get_application_name()

    def get_sync_path(self):
        return "/api/sync/data"

    def get_base_url(self):
        application_server = None
        if self.external_mode == 'server_auth':
            application_server = self.application_server_auth_id.application_server_id
        elif self.external_mode == 'server_path':
            application_server = self.application_server_path_id.application_server_auth_id.application_server_id
        if application_server:
            return application_server.get_endpoint_url()
        return super(ExternalServerSync, self).get_base_url()

    def get_db_uid_username_password(self):
        rec = self.ensure_one()
        if rec.external_mode == 'server_auth':
            return rec.application_server_auth_id.get_db_uid_username_password()

        if rec.external_mode == 'server_path':
            return rec.application_server_path_id.application_server_auth_id.get_db_uid_username_password()

        return super(ExternalServerSync, self).get_db_uid_username_password()

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
        if not self.get_application_name():
            raise UserError(_("Application Server is not set for External Server Sync '%s'") % rec.name)

        if rec.external_mode == 'server_auth':
            return rec.application_server_auth_id.get_external_data(
                model_name, domain=domain, fields=fields, offset=offset,
                limit=limit, count=count, object_id=object_id,
                context=context, path=rec.get_sync_path()
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

    def get_auth_config(self):
        config = super(ExternalServerSync, self).get_auth_config()
        application_server_auth = None
        if self.external_mode == 'server_auth':
            application_server_auth = self.application_server_auth_id

        if self.external_mode == 'server_path':
            application_server_auth = self.application_server_path_id.application_server_auth_id

        if application_server_auth:
            config['token_endpoint_url'] = application_server_auth.rest_url(application_server_auth.rest_login_path())
        # config['token_endpoint_url']
        # auth_type = self.server_sync_id.auth_type
        # token_key = self.server_sync_id.token_key
        # access_token = self.server_sync_id.token_value
        # if auth_type == 'token':
        #     auth_type = self.server_sync_id.token_in
        # db, uid, username, password = self.get_db_uid_username_password()
        return config
        # return {
        #     'db': db,
        #     'uid': uid,
        #     'username': username,
        #     'password': password,
        #     'auth_mode': auth_type,
        #     'token_key': token_key,
        #     'access_token': access_token,
        #     'token_endpoint_url': None
        # }
