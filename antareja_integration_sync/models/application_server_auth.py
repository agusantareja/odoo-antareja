# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)


def get_endpoint_model_name_path(path, model_name):
    if not path or path == '/':
        path = ''
    return f"{path}/{model_name}"


class ApplicationServerAuth(models.Model):
    _inherit = 'application.server.auth'

    def get_application_name(self):
        return self.application_server_id.name

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
            is_single_object = False
            if object_id and isinstance(object_id, int):
                path_model = f"{path_model}/{object_id}"
                is_single_object = True
            else:
                if object_id and isinstance(object_id, list):
                    params['ids'] = str(object_id)
                if domain:
                    params['domain'] = str(domain)
                if offset is not None:
                    params['offset'] = offset
                if limit is not None:
                    params['limit'] = limit
                if count:
                    params['count'] = True
            if context:
                params['context'] = str(context)
            if fields is not None:
                params['fields'] = str(fields)
            response = rec.rest_get(path_model, params=params)
            response.raise_for_status()
            if count:
                return response.json().get("count", 0)
            if is_single_object:
                return response.json() or []
            return response.json().get("results", [])
