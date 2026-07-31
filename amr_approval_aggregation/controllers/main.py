# -*- coding: utf-8 -*-

import logging
from odoo import api, http, SUPERUSER_ID, _
from odoo.http import request
from odoo import registry as registry_get
# from odoo.addons.cni_api.controllers.main import check_valid_token
from odoo.addons.antareja_base.tools.rest import valid_response, invalid_response, get_body_json
from odoo.addons.antareja_token.tools.utils import check_token_authorization

try:
    import simplejson as json
except ImportError:
    import json

_logger = logging.getLogger(__name__)


class MainController(http.Controller):

    @http.route(['/api/v1/approval/aggregation', '/api/intra/mobile/approval'], methods=['POST'], type='http',
                auth='machine', csrf=False)
    def post_approval(self, **post):
        data = post or get_body_json()
        if not data:
            return invalid_response(400, "no_data", "enpty data")
        new_registry = registry_get(request.session.get('db'))
        with new_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            result = env['mobile.approval'].api_create_request(**data)

        return valid_response(200, result)

    @http.route(['/api/v1/approval/aggregation', '/api/intra/mobile/approval'], methods=['GET'], type='http',
                auth='machine', csrf=False)
    def get_approval(self, **post):
        data = post
        new_registry = registry_get(request.session.get('db'))
        with new_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            result = env['mobile.approval'].api_get_approvals(**data)
        return valid_response(200, result)

    @http.route(['/api/v1/approval/aggregation/distinct', '/api/intra/mobile/approval/distinct'], methods=['GET'],
                type='http', auth='machine', csrf=False)
    def get_approval_distinct(self, **post):
        data = post
        new_registry = registry_get(request.session.get('db'))
        with new_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            if 'user_email' in data:
                domain = [('user_id.partner_id.email', '=', data['user_email'])]
            else:
                domain = []

            if 'field_select' not in data:
                return invalid_response(400, "field_select parameter not found", "Invalid data query")
            else:
                field_select = data['field_select']

            result_group = env['mobile.approval'].read_group(
                domain=domain,
                fields=[field_select],
                groupby=[field_select],
                lazy=False
            )
            result = [str(rec.get(field_select, "")) for rec in result_group]
        return valid_response(200, result)
