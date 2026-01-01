# -*- coding: utf-8 -*-

import requests
import datetime
from odoo import models, fields, api, _
import json
import traceback
import logging

_logger = logging.getLogger(__name__)


def get_endpoint_model_name_path(path, model_name):
    if not path or path == '/':
        path = ''
    return f"{path}/{model_name}"


class ApplicationServerAuth(models.Model):
    _inherit = 'application.server.auth'

    # _inherit = ['application.server.auth.odoo.rcp.mixin',
    #             'ir.config_parameter.able.mixin']
    #
    # active = fields.Boolean(default=True)
    # name = fields.Char()
    # application_server_id = fields.Many2one('application.server')
    # application_server_path_ids = fields.One2many('application.server.path', 'application_server_auth_id')
    # auth_type = fields.Selection([
    #     ('odoo-rcp', 'Odoo RCP'),
    #     ('rest-token', 'Rest Token'),
    # ], default='rest-token')
    #
    # def get_rest_token(self):
    #     return self.get_value_config_param(value_without_config_param=self.rest_token)
    #
    # def rest_endpoint_url(self):
    #     return self.application_server_id.endpoint

    def get_external_data(self, model_name, domain=None, fields=None, offset=None, limit=None, count=False,
                          object_id=None, context=None, path=None):

        rec = self
        if rec.auth_type in ['odoo-rcp', 'jwt-odoo-rcp']:
            db, uid, password = rec.jsonrpc_authenticate()
            if object_id and isinstance(object_id, int):
                method = 'read'
                args = [[object_id]]
                kw = {'fields': fields}
            elif count:
                method = 'search'
                args = [domain]
                kw = {'count': True}
            else:
                method = 'search_read'
                args = [domain]
                kw = {'fields': fields, 'offset': offset, 'limit': limit}

            if context:
                kw['context'] = context

            return rec.jsonrpc_call(
                model_name, method, args, kw=kw, db=db, uid=uid, password=password
            )
        else:
            path_model = get_endpoint_model_name_path(path, model_name)
            params = {}
            if object_id and isinstance(object_id, int):
                path_model = f"{path_model}/{object_id}"
            else:
                if domain:
                    params['domain'] = str(domain)
                if fields is not None:
                    params['fields'] = str(fields)
                if offset is not None:
                    params['offset'] = offset
                if limit is not None:
                    params['limit'] = limit
                if count:
                    params['count'] = True
                if context:
                    params['context'] = str(context)
            response = rec.rest_get(path_model, params=params)
            response.raise_for_status()
            if count:
                return response.json().get("count", 0)
            return response.json().get("results", [])
