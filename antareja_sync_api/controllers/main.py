
try:
    import simplejson as json
except ImportError:
    import json
from odoo import http
from odoo.addons.antareja_base.tools.rest import *
from odoo.addons.antareja_token.tools.utils import *

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
        '/api/sync/data/<model_name>/<id>'
    ], type='http', auth="none", methods=['GET'], csrf=False)
    @check_token_authorization(setup_session=True)
    def rest_api_sync_data(self, model_name=False, id=False, **post):
        Model = request.env['ir.model']
        Model_id = Model.sudo().search([('model', '=', model_name)], limit=1)
        if Model_id:
            if Model_id.is_read_sync_api():
                if id:
                    return object_read_one(model_name, id, post, status_code=200, filter_fields=readable_fields)
                else:
                    return object_read(model_name, post, status_code=200, filter_fields=readable_fields)
            else:
                return rest_api_unavailable(model_name)
        return modal_not_found(model_name)
