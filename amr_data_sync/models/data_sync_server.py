# -*- coding: utf-8 -*-

import requests
from odoo import models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ExternalServerSync(models.Model):
    _name = 'external.server.sync'

    active = fields.Boolean(default=True)
    name = fields.Char()
    app_name = fields.Char("Application Name")

    odoo_server_db = fields.Char()
    odoo_server_uid = fields.Integer(readonly=True)

    base_url = fields.Char()
    path = fields.Char(default='/api')
    auth_type = fields.Selection([
        ('basic', 'Basic'),
        ('token', 'Key Token'),
    ], default='basic')

    basic_auth_username = fields.Char()
    basic_auth_password = fields.Char()

    token_in = fields.Selection([(
        'header', 'Header'), ('param', 'Parameter'), ('body', 'Body')
    ], default='header')
    token_key = fields.Char(
        default='access_token'
    )
    token_value = fields.Char()

    # user_id = fields.Many2one('res.users')
    def get_endpoint_url(self):
        return f"{self.base_url}{self.path}"

    def get_endpoint_model_name_url(self, model_name):
        return f"{self.get_endpoint_url()}/{model_name}"

    def get_headers_request(self):
        return {
            self.token_key: self.token_value,
            "Accept": "application/json"
        }

    def get_model_name_data(self, model_name, ref_id):
        url = self.get_endpoint_model_name_url(model_name) + f"/{ref_id}"
        headers = self.get_headers_request()
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise UserError(f"Failed to fetch data: {response.status_code} - {response.text}")

        return response.json()[0]

    def get_db_name(self):
        url = f"{self.base_url}/api/sync/authenticate"
        response = requests.post(url, data={
            'login': self.basic_auth_username,
            'password': self.basic_auth_password,
        })
        response.raise_for_status()
        json_data = response.json()
        self.odoo_server_db = json_data.get('db')
        self.odoo_server_uid = json_data.get('uid')

    def get_db_name_uid_password(self):
        if self.odoo_server_db and self.odoo_server_uid:
            return self.odoo_server_db, self.odoo_server_uid, self.basic_auth_password
        return self.sync_authenticate()

    def sync_authenticate(self):
        url = f"{self.base_url}/api/sync/authenticate"
        response = requests.post(url, data={
            'login': self.basic_auth_username,
            'password': self.basic_auth_password,
        })
        response.raise_for_status()
        json_data = response.json()
        odoo_server_db = json_data.get('db')
        odoo_server_uid = json_data.get('uid')
        return odoo_server_db, odoo_server_uid, self.basic_auth_password

    def action_get_db_name(self):
        self.get_db_name()

    def action_authenticate(self):
        try:
            if self.odoo_server_db:
                self.jsonrpc_authenticate()
            else:
                self.sync_authenticate()
        except Exception as e:
            _logger.error("Authentication failed: %s", str(e))
            raise UserError(_("Authentication failed: %s") % str(e))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sukses',
                'message': 'Auntentikasi berhasil.',
                'type': 'success',  # bisa: success / warning / danger / info
                'sticky': False,  # True = tidak hilang otomatis
            }
        }

    def jsonrpc_authenticate(self):
        if not self.odoo_server_db:
            self.get_db_name()

        if self.odoo_server_db:
            url = self.base_url + "/jsonrpc"
            db = self.odoo_server_db
            username = self.basic_auth_username
            password = self.basic_auth_password

            # 1. Authenticate
            auth_payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [db, username, password, {}]
                },
                "id": 1,
            }
            res = requests.post(url, json=auth_payload).json()
            self.odoo_server_uid = res.get("result")

    def jsonrpc_call(self, model, method, args, kw=None, db=None, uid=None, password=None):
        if db is None or uid is None or password is None:
            db, uid, password = self.get_db_name_uid_password()

        url = self.base_url + "/jsonrpc"
        args = [
            db,
            uid,
            password,
            model,
            method,
            args,
            kw
        ]
        obj_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": args,
            },
            "id": 2,
        }
        try:
            response = requests.post(url, json=obj_payload)
            response.raise_for_status()
            json_data = response.json()
            if "error" in json_data:
                raise Exception(f"Odoo Error: {json_data['error']}")
            return json_data.get("result")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network Error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected Error: {str(e)}")


    def get_external_data(self, model_name, domain=None, fields=None, offset=None, limit=None, count=False,
                          object_id=None, context=None):
        if self.auth_type == 'basic':
            db, uid, password = self.get_db_name_uid_password()
        else:
            db = uid = password = None

        if db:
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

            return self.jsonrpc_call(
                model_name,
                method,
                args,
                kw=kw,
                db=db,
                uid=uid,
                password=password
            )
        else:
            url = self.get_endpoint_model_name_url(model_name)
            headers = self.get_headers_request()
            params = {}
            if object_id and isinstance(object_id, int):
                url = f"{url}/{object_id}"
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
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            if count:
                return response.json().get("count", 0)
            return response.json().get("results", [])
