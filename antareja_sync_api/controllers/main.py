# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.antareja_base.tools.rest import modal_not_found,rest_api_unavailable,object_read,object_read_one
from odoo.addons.antareja_token.tools.utils import check_token_authorization

import logging

_logger = logging.getLogger(__name__)

def readable_fields(model_name, fields):
    if not fields:
        Model = request.env['ir.model']
        Model_id = Model.sudo().search([('model', '=', model_name)], limit=1)
        fields = Model_id.readable_fields([])
    return fields


class ControllerSync(http.Controller):

    @http.route([
        '/api/sync/data/<model_name>',
        '/api/sync/data/<model_name>/<int:id>'
    ], type='http', auth="none", methods=['GET'], csrf=False)
    @check_token_authorization(setup_session=True)
    def rest_api_sync_data(self, model_name, id=None, **kwargs):
        Model = request.env['ir.model']
        Model_id = Model.sudo().search([('model', '=', model_name)], limit=1)
        if not Model_id:
            return modal_not_found(model_name)
        if Model_id.is_read_sync_api():
            return rest_api_unavailable(model_name)
        if id:
            return object_read_one(model_name, id, kwargs, status_code=200, filter_fields=readable_fields)
        else:
            return object_read(model_name, kwargs, status_code=200, filter_fields=readable_fields)
