# -*- coding: utf-8 -*-

import logging
import werkzeug
from odoo import http, fields, SUPERUSER_ID, _
from odoo.http import request
from werkzeug import url_encode

_logger = logging.getLogger(__name__)

def validate_jwt(token):
    secret = request.env['ir.config_parameter'].sudo().get_param('jwt.secret')
    algorithm = 'HS256'
    import jwt
    from jwt import ExpiredSignatureError, InvalidTokenError
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm]
        )
        return payload
    except ExpiredSignatureError:
        return None
    except InvalidTokenError:
        return None


class ControllerMobileAccess(http.Controller):

    @http.route(['/web_mobile_access',], type='http', auth='none', methods=['GET'], csrf=False)
    def web_mobile_access(self, mobile_token=None, **kw):

        if request.session.uid:
            _logger.info("Sudah login")
        else:
            token_data = request.env['mobile.access.token'].validate(mobile_token)
            token_data and request.session.authenticate(request.session.db, uid=token_data['uid'], password=mobile_token)
            #return http.redirect_with_hash('/web')
        if kw:
            url = "/web#%s"% url_encode(kw)
        else:
            url = "/web"
        return werkzeug.utils.redirect(url)

    @http.route('/api/profile', type='json', auth='none', methods=['POST'])
    def api_profile(self):
        auth = request.httprequest.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return {'error': 'Missing token'}

        token = auth.replace('Bearer ', '')
        payload = validate_jwt(token)

        if not payload:
            return {'error': 'Invalid or expired token'}

        user_id = payload.get('uid')
        user = request.env['res.users'].sudo().browse(user_id)
        if not user.exists():
            return {'error': 'User not found'}

        # 🔐 set user context
        request.uid = user.id

        return {
            'uid': user.id,
            'name': user.name,
            'login': user.login,
            'db': user.login,
        }
