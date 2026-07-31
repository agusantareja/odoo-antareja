# -*- coding: utf-8 -*-

import json
import logging

from odoo.http import Controller, Response, request, route

_logger = logging.getLogger(__name__)

from odoo import http
from odoo.http import request

import os
import base64

class PasskeyController(http.Controller):

    @http.route('/auth/passkey/register/begin',type='json', auth='user',csrf=False)
    def register_begin(self):
        user = request.env.user
        challenge = base64.urlsafe_b64encode(os.urandom(32)).decode()
        request.session['passkey_challenge'] = challenge

        return {
            'challenge': challenge,
            'rp': {
                'name': 'My Odoo'
            },
            'user': {
                'id': str(user.id),
                'name': user.login,
                'displayName': user.name,
            }
        }

    @http.route('/auth/passkey/register/finish',type='json',auth='user',csrf=False)
    def register_finish(self, credential):
        challenge = request.session.get('passkey_challenge')

        # verify credential di sini

        request.env['res.users.passkey'].sudo().create({
            'user_id': request.env.user.id,
            'credential_id': 'xxxx',
            'public_key': 'yyyy',
        })

        return {
            'success': True
        }