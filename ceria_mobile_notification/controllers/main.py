# -*- coding: utf-8 -*-

import ast
import logging
import datetime
import werkzeug.urls
import werkzeug.utils
from odoo import api, http, fields, SUPERUSER_ID, _
from odoo.http import request
from odoo import registry as registry_get

from odoo.addons.cni_api.controllers.main import check_valid_token
try:
    import simplejson as json
except ImportError:
    import json

_logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        if isinstance(obj, datetime.datetime):
            return fields.Datetime.to_string(obj)
        if isinstance(obj, datetime.date):
            return fields.Date.to_string(obj)
        return json.JSONEncoder.default(self, obj)

def valid_response(status, data):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(data, cls=JSONEncoder),
    )


def invalid_response(status, error, info):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps({
            'error': error,
            'error_desc': info,
        }),
    )
class MainController(http.Controller):
   
    @http.route('/api/intra/mobile/notification', methods=['POST'], type='http', auth='none', csrf=False)
    @check_valid_token
    def post_mobile_notification(self,**post):
        data = {}
        result = False
        data_str = request.httprequest.data.decode("utf-8")
        if data_str:
            try:
                data = json.loads(data_str)
                if isinstance(data, str):
                    data = json.loads(data)
            except:
                pass
        if data:
            new_registry = registry_get(request.session.get('db'))
            with new_registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                notif = env['ceria.mobile.notification'].create_payload(**data)
                if notif:
                    notif.process()
                    if notif.state=='error':
                        return invalid_response(400, "Can not process notification", notif.errors_message)

                    result = {
                        'status' : 'success',
                        'message': 'Created Notification ID %s'%notif.id,
                    }
                else:
                    return invalid_response(400,"Can not crate notification","")

                if data.get('send_force'):
                    notif.send()
                    if notif.state=='send_error':
                        return invalid_response(
                            506,
                            'send_error',
                            'Created Notification ID %s : \n error: %s' %(notif.id,notif.errors_message))
                    else:
                        result = {
                            'status': 'success',
                            'message': 'Notification ID %s send' % notif.id,
                        }

        return valid_response(200,result)

