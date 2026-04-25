# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.antareja_base.tools.rest import object_read
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
        '/api/event/data',
    ], type='http', auth="none", methods=['GET'], csrf=False)
    @check_token_authorization(setup_session=False)
    def rest_api_event_data(self, **kwargs):
        return object_read('internal.data.event', kwargs, status_code=200)