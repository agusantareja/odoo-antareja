# -*- coding: utf-8 -*-

import functools
import ast

import werkzeug

from odoo.exceptions import AccessDenied

try:
    import simplejson as json
except ImportError:
    import json
import odoo
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

db_name = odoo.tools.config.get('db_name')
if not db_name:
    _logger.warning("Warning: To proper setup OAuth - it's necessary to "
                    "set the parameter 'db_name' in odoo config file!")

def get_http_body():
    data = request.httprequest.data.decode("utf-8")  # raw body string
    try:
        json_data = json.loads(data)  # parse manual
    except Exception:
        json_data = {}
    return json_data

class ControllerIntegration(http.Controller):

    @http.route([
        '/api/integration/db_name',
    ], type='http', auth="none", methods=['GET'], csrf=False)
    def rest_api_integration(self, **post):

        data = {
            'db': db_name,
        }
        return werkzeug.wrappers.Response(
        status='200',
        content_type='application/json; charset=utf-8',
        response=json.dumps(data),
    )

    @http.route([
        '/api/integration/authenticate',
    ], type='http', auth="none", methods=['POST'], csrf=False)
    def rest_api_integration_authenticate(self, **post):
        body = get_http_body()
        login = post.get('login') or body.get('login')
        password = post.get('password') or body.get('password')
        session = request.session
        try:
            session.authenticate(db_name, login, password)
        except AccessDenied as e:
            return werkzeug.wrappers.Response(
                status='401',
                content_type='application/json; charset=utf-8',
                response=json.dumps({
                    'error': 'access_denied',
                    'error_desc': str(e),
                }),
            )

        data = {
            'uid': session.uid,
            'sid': session.sid,
            'db': session.db,
            'session_token': session.session_token,
        }
        return werkzeug.wrappers.Response(
            status='200',
            content_type='application/json; charset=utf-8',
            response=json.dumps(data),
        )
