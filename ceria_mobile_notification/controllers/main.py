# -*- coding: utf-8 -*-

import datetime
import json
import logging

from odoo import fields
from odoo.http import Controller, Response, request, route

from odoo.addons.cni_api.controllers.main import check_valid_token

_logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        if isinstance(obj, datetime.datetime):
            return fields.Datetime.to_string(obj)
        if isinstance(obj, datetime.date):
            return fields.Date.to_string(obj)
        return super().default(obj)

def valid_response(status, data):
    return Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(data, cls=JSONEncoder),
    )

def invalid_response(status, error, info):
    return Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps({
            'error': error,
            'error_desc': info,
        }),
    )


class MainController(Controller):
   
    @route('/api/intra/mobile/notification', methods=['POST'], type='http', auth='none', csrf=False)
    @check_valid_token
    def post_mobile_notification(self, **kwargs):
        data = {}
        data_str = request.httprequest.data.decode("utf-8")
        if not data_str:
            return invalid_response(400, "No Data", "Request data is empty")
        try:
            data = json.loads(data_str)
            if isinstance(data, str):
                data = json.loads(data)
        except:
            return invalid_response(400, "Invalid JSON", "Request data is not a valid JSON format")

        notif = request.env['ceria.mobile.notification'].sudo().create_payload(**data)
        if not notif:
            return invalid_response(400,"Cannot create notification","")

        notif.process()
        if notif.state == 'error':
            return invalid_response(400, "Cannot process notification", notif.errors_message)

        result = {
            'status': 'success',
            'message': 'Created notification ID %s' % notif.id,
        }
        if not data.get('send_force'):
            return valid_response(200, result)

        notif.send()
        if notif.state == 'send_error':
            return invalid_response(
                506,
                'send_error',
                'Created notification ID %s, error sending: %s' % (notif.id, notif.errors_message)
            )

        result['message'] = 'Notification ID %s sent' % notif.id
        return valid_response(200, result)
