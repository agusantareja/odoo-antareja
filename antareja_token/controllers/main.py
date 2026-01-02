# -*- coding: utf-8 -*-

import logging
import werkzeug
import json
from odoo import http, fields, SUPERUSER_ID, _
from odoo.http import request
from werkzeug import url_encode

_logger = logging.getLogger(__name__)


class ControllerMobileAccess(http.Controller):

    @http.route(['/web_token_access'], type='http', auth='none', methods=['GET'], csrf=False)
    def web_token_access(self, token_access=None, redirect=None,**kw):

        if request.session.uid:
            _logger.info("Sudah login")
        else:
            token_data = request.env['antareja.token'].validate(token_access)
            if token_data and token_data.get('uid'):
                request.session.authenticate(request.session.db, uid=token_data['uid'], password=token_access)
            # return http.redirect_with_hash('/web')
        if redirect:
            url=redirect
        elif kw:
            url = "/web#%s" % url_encode(kw)
        else:
            url = "/web"
        return werkzeug.utils.redirect(url)

    @http.route("/api/application/login", type="http", auth="none", methods=["POST"], csrf=False)
    def login(self, login=None, password=None):
        if not login or not password:
            return self._error("Invalid login or password")

        uid = request.session.authenticate(
            request.session.db, login, password
        )
        if not uid:
            return self._error("Invalid login or password")
        kw = request.env["antareja.token"].login(uid)
        return self._success(**kw)

    @http.route('/api/application/profile', type='http', auth='none', methods=['POST'], csrf=False)
    def api_profile(self):

        auth = request.httprequest.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return self._error("Missing token")

        token = auth.replace('Bearer ', '')
        payload = request.env['antareja.token'].validate(token)

        if not payload or not payload.get('uid'):
            return self._error("Invalid or expired token")

        uid = payload.get('uid')
        user = request.env['res.users'].sudo().browse(uid)
        if not user.exists():
            return self._error("User not found")

        # set user context
        request.uid = user.id

        return self._success(
            uid=user.id,
            name=user.name,
            login=user.login,
            db=request.session.db,
        )

    @http.route('/api/application/refresh', type='http', auth='none', methods=['POST'], csrf=False)
    def refresh_grant(self, refresh_token=None):

        if not refresh_token:
            return self._error("invalid_request")

        payload = request.env['antareja.token'].validate(refresh_token,refresh_token=True)

        if not payload or not payload.get('token'):
            return self._error("Invalid or expired token")

        token = payload.get('token')

        Refresh = request.env["antareja.refresh.token"].sudo()

        rec = Refresh.search([
            ("token", "=", token),
            ("revoked", "=", False)
        ], limit=1)

        if not rec or rec.expires_at < fields.Datetime.now():
            return self._error("invalid_grant")

        # revoke old token
        rec.write({"revoked": True})

        kw = request.env["antareja.token"].login(rec.user_id.id)
        return self._success(**kw)

    def _success(self, **kwargs):
        return request.make_response(
            json.dumps(kwargs),
            headers=[("Content-Type", "application/json")]
        )

    def _error(self, error):
        return request.make_response(
            json.dumps({"error": error}),
            status=400,
            headers=[("Content-Type", "application/json")]
        )
