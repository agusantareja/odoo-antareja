# -*- coding: utf-8 -*-

import logging
import json

from odoo.http import request
from odoo.service import security
from functools import wraps
from werkzeug.wrappers import Response
from odoo.addons.antareja_base.tools.rest import invalid_response

_logger = logging.getLogger(__name__)

"""
2025-08-28 03:03:45,369 28428 INFO DEV_13_INTRA_2_OCNI-00797 odoo.addons.base.models.ir_http: Exception during request Authentication. 
Traceback (most recent call last):
  File "{odoo_home}\odoo\addons\base\models\ir_http.py", line 115, in _authenticate
    request.session.check_security()
  File "{odoo_home}\odoo\http.py", line 1055, in check_security
    if not security.check_session(self, env):
  File "{odoo_home}\odoo\service\security.py", line 27, in check_session
    if expected and odoo.tools.misc.consteq(expected, session.session_token ):
TypeError: unsupported operand types(s) or combination of types: 'str' and 'NoneType'

"""
# _original_check_security = OpenERPSession.check_security
#
#
# def custom_check_security(self):
#     if request and request.httprequest and request.httprequest.path:
#         path = request.httprequest.path
#         if path and self.uid and not self.session_token:
#             _logger.warning("Session tanpa token dianggap expired API route %s", path)
#             raise SessionExpiredException("Session expired")
#
#     _original_check_security(self)
#
#
# # Replace method
# OpenERPSession.check_security = custom_check_security


def set_session(login, uid, session_token=None):
    session = request.session
    session.rotate = True
    session.uid = uid
    session.login = login
    if login or uid:
        session.session_token = security.compute_session_token(session, request.env)
    else:
        session.session_token = session_token
    if not session.session_token:
        request.update_env()
        # request.uid = None
        session.uid = None
        session.login = None
    else:
        request.update_env(user=request.session.uid)
        # request.uid = uid
        #request.disable_db = False
        #session.get_context()


def get_bearer_token():
    auth = request.httprequest.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    return auth.split(" ", 1)[1]


def make_response_error(status=400, error="", error_description=""):
    return Response(
        json.dumps({"error": error, 'error_description': error_description}),
        status=status,
        headers=[("Content-Type", "application/json")]
    )


def check_token_authorization(_func=None,*,setup_session=False, header_name=('token','access_token'), param_name=None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            error = {}
            session = request.session
            uid = session.uid or request.uid
            login = session.login
            session_token = session.session_token
            # ambbil semua kemungkin token yang ada
            token_list = [get_bearer_token()]
            header_names = []
            if header_names:
                if isinstance(header_name,str):
                    header_names=[header_names]
                elif isinstance(header_name,(list, tuple)):
                    header_names =header_name
            for name in header_names:
                token_list.append(request.httprequest.headers.get(name))
            if param_name:
                params = []
                if isinstance(param_name, str):
                    params.append(param_name)
                elif isinstance(param_name, (list, tuple)):
                    params.extend(param_name)
                for p in params:
                    token_list.append(request.params.get(p))
                    token_list.append(kwargs.get(p))

            tokens = set(token_list)
            accept_authorization = False
            for t in tokens:
                if not t:
                    continue
                token_data = request.env['antareja.token'].sudo().validate(t)
                if token_data and token_data.get('uid'):
                    uid = token_data['uid']
                    login = token_data.get('username') or token_data.get('sub')
                    if uid and login:
                        accept_authorization = True
                        if setup_session:
                            set_session(login, uid)
                if accept_authorization:
                    break
            if not setup_session and not accept_authorization:
                for t in tokens:
                    accept_authorization = request.env['antareja.token'].sudo().client_token_validation(t)
                    if accept_authorization:
                        break
            if not accept_authorization:
                return invalid_response(
                    401, error.get("error", "invalid_token"),
                    error.get("error_description", "The token is invalid or expired.")
                )
            result = func(self, *args, **kwargs)
            if setup_session:
                # set kembali session sebelumnya
                set_session(uid, login, session_token)
            return result
        return wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)

