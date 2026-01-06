# -*- coding: utf-8 -*-

import logging
import werkzeug
from odoo import http, fields
from odoo.http import request
from werkzeug import url_encode
from ..tools.utils import set_session, get_bearer_token
from odoo.addons.antareja_base.tools.rest import valid_response, invalid_response

_logger = logging.getLogger(__name__)


def _password_grant(data):
    user = request.env['res.users'].sudo().search([
        ('login', '=', data.get('username'))
    ], limit=1)

    if user:
        try:
            user.with_user(user)._check_credentials(data.get('password'))
        except Exception:
            return invalid_response(200, "invalid_grant")
    else:
        return invalid_response(200, "invalid_grant")

    kw = request.env["antareja.token"].login(user.id)
    return valid_response(200, kw)


class ControllerMobileAccess(http.Controller):

    @http.route(['/web_token_access'], type='http', auth='none', methods=['GET'], csrf=False)
    def web_token_access(self, token_access=None, redirect=None, **kw):
        def get_valid_token_payload(token, env):
            token_data = env['antareja.token'].validate(token)
            if token_data and token_data.get('uid'):
                return token_data
            payload = env['antareja.token.audience'].validate(token)
            if payload and payload.get('uid'):
                return payload
            return None

        if request.session.uid:
            _logger.info("Sudah login")
        else:
            token_data = get_valid_token_payload(token_access, request.env)
            if token_data and token_data.get('uid'):
                uid = token_data['uid']
                login = token_data.get('username') or token_data.get('sub')
                set_session(login, uid)
        if redirect:
            url = redirect
        elif kw:
            url = "/web#%s" % url_encode(kw)
        else:
            url = "/web"
        return werkzeug.utils.redirect(url)

    @http.route('/application/token', type='http', auth='none', methods=['POST'], csrf=False)
    def api_token(self, **kwargs):
        grant_type = kwargs.get('grant_type')

        if grant_type == 'password':
            return _password_grant(kwargs)

        if grant_type == 'refresh_token':
            return self._refresh_grant(kwargs.get('refresh_token'))

        if grant_type == 'trusted_token':
            return self._trusted_grant(kwargs.get('access_token'))

        return invalid_response(200, "unsupported_grant_type")

    @http.route('/application/profile', type='http', auth='none', methods=['POST'], csrf=False)
    def api_profile(self):
        token = get_bearer_token()
        if token:
            payload = request.env['antareja.token'].validate(token) or {}
            active = False
            if payload and payload.get('uid'):
                uid = payload.get('uid')
            if uid:
                user = request.env['res.users'].sudo().browse(request.uid)
                active = user.exists()
        if active:
            data = dict(payload)
            data.update(
                active=True,
                uid=user.id,
                user_id=user.id,
                name=user.name,
                login=user.login,
                db=request.session.db,
            )
            return valid_response(200, data)
        else:
            return valid_response(200, {'active': active})

    @http.route('/application/refresh', type='http', auth='none', methods=['POST'], csrf=False)
    def api_application_refresh(self, refresh_token=None):
        return self._refresh_grant(refresh_token)

    @http.route('/application/introspect', type='http', auth='none', methods=['POST'], csrf=False)
    def api_application_introspect(self):
        active = False
        token = get_bearer_token()
        if token:
            payload = request.env['antareja.token'].validate(token)
            if payload and payload.get('uid'):
                uid = payload.get('uid')
                user = request.env['res.users'].sudo().browse(uid)
                active = user.exists()

        if active:
            data = dict(payload)
            data.update(
                active=active,
                uid=user.id,
                user_id=user.id,
                name=user.name,
                login=user.login,
                db=request.session.db,
            )
            return valid_response(200, data)
        else:
            return valid_response(200, {'active': active})

    def _trusted_grant(self, token_access):
        payload = self.env['antareja.token.audience'].validate(token_access)
        if payload and payload.get('uid'):
            kw = request.env["antareja.token"].login(payload['uid'])
            return valid_response(200, kw)
        else:
            return invalid_response(200, "invalid_grant")

    def _refresh_grant(self, refresh_token=None):
        if not refresh_token:
            return invalid_response(200, "invalid_request")

        payload = request.env['antareja.token'].validate(refresh_token, refresh_token=True)

        if not payload or not payload.get('token'):
            return invalid_response(200, "invalid_grant", "Invalid or expired token")

        token = payload.get('token')

        Refresh = request.env["antareja.refresh.token"].sudo()

        rec = Refresh.search([
            ("token", "=", token),
            ("revoked", "=", False)
        ], limit=1)

        if not rec or rec.expires_at < fields.Datetime.now():
            return invalid_response(200, "invalid_grant")

        # revoke old token
        rec.write({"revoked": True})

        kw = request.env["antareja.token"].login(rec.user_id.id)
        return valid_response(200, kw)
