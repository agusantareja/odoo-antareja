# -*- coding: utf-8 -*-

import logging
import json
import base64

import io
import qrcode

import uuid
from odoo import http, fields
from odoo.http import request
import jwt
import datetime

from werkzeug.wrappers import Response

from odoo import api, http, fields
from odoo.http import request
from werkzeug.exceptions import BadRequest, Conflict, NotFound
from werkzeug.utils import redirect
from odoo.addons.amr_resource.exceptions import handle_exception

_logger = logging.getLogger(__name__)


class ControllerToken(http.Controller):

    def valid_response(self, status, data):
        return Response(
            status=status,
            content_type='application/json; charset=utf-8',
            response=json.dumps(data),
        )

    def invalid_response(self, status, error, info=""):
        return self.make_response(status=status, error=error, error_description=info)

    def make_response(self, status=200, **payload):
        return Response(
            response=json.dumps(
                payload or {"error": "unknown_error", "error_description": "An unknown error occurred."}),
            status=status,
            headers=[("Content-Type", "application/json")]
        )

    @api.model
    def generate_qr(self, deep_link, version=2, box_size=10, border=1):
        qr = qrcode.QRCode(version=version, box_size=box_size, border=border)
        qr.add_data(deep_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return request.make_response(
            buffer.getvalue(),
            headers=[
                ('Content-Type', 'image/png')
            ]
        )

    @http.route('/qr/<deep_link>', type='http', auth='public', methods=['GET'], csrf=False)
    def qr_digital_signature(self, deep_link, version=2, box_size=10, border=2):
        signature = request.env['amr.signature'].search([('name', '=', deep_link)])
        if not signature:
            raise NotFound
        return self.generate_qr(signature.deep_link, version=version, box_size=box_size, border=border)

    @http.route('/dl', type='http', auth='jwt', methods=['POST'], csrf=False)
    def create_digital_signature(self, token, **kwargs):
        try:
            signature = request.env['amr.signature'].sudo().create_with_retry(token)
        except ValueError:
            _logger.exception("Error")
            raise BadRequest
        except Exception:
            _logger.exception("Error")
            raise Conflict

        return self.generate_qr(signature.deep_link)

    @http.route('/dl/<deep_link>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_digital_signature(self, deep_link, version=2, box_size=10, border=2):
        signature = request.env['amr.signature'].search([('name', '=', deep_link)])
        if not signature:
            raise NotFound

        accept = request.httprequest.headers.get('Accept', '')
        user_agent = request.httprequest.headers.get('User-Agent', '')

        # cek support jwt mime
        supports_jwt = (
                'application/jwt' in accept
        )
        if supports_jwt:
            return Response(
                signature.jwt_token,
                content_type='application/jwt',
                status=200
            )
        if 'Android' in user_agent:
            return redirect(
                'intent://digitalsignature?token=%s#Intent;'
                'scheme=digitalsignature;'
                'package=tech.ramdan.agus.app;'
                'end' % signature.jwt_token
            )

        fallback_url = '/view/dl?token=%s' % signature.name
        return redirect(fallback_url)

    @http.route('/view/dl/<deep_link>', type='http', auth='public_or_jwt', methods=['GET'], csrf=False)
    def view_digital_signature(self, deep_link, **kwargs):
        signature = request.env['amr.signature'].search([('name', '=', deep_link)])
        if not signature:
            raise NotFound

        accept = request.httprequest.headers.get('Accept', '')
        user_agent = request.httprequest.headers.get('User-Agent', '')

        # TODO
        fallback_url = 'https://example.com/open-app?token=%s' % signature.jwt_token
        return
