# -*- coding: utf-8 -*-

import logging
import json
import base64

from odoo.http import request
from odoo.service import security
from functools import wraps
from werkzeug.wrappers import Response
from odoo.addons.antareja_base.tools.rest import invalid_response

_logger = logging.getLogger(__name__)


# v16 handle session berbeda dengan 13
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


def get_basic_auth():
    auth = request.httprequest.headers.get('Authorization')
    if not auth:
        return None, None

    try:
        scheme, encoded = auth.split(' ', 1)
        if scheme.lower() != 'basic':
            return None, None

        decoded = base64.b64decode(encoded).decode('utf-8')
        return decoded.split(':', 1)
    except Exception:
        return None, None


def make_response_error(status=400, error="", error_description=""):
    return Response(
        json.dumps({"error": error, 'error_description': error_description}),
        status=status,
        headers=[("Content-Type", "application/json")]
    )


def check_token_authorization(_func=None, *, setup_session=False, header_name=('token', 'access_token'), param_name=None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            error = {}
            session = request.session
            save_uid = session.uid or request.uid
            save_login = session.login
            session_token = session.session_token
            accept_authorization = False
            try:
                username, password = get_basic_auth()
                uid = request.session.authenticate(
                    request.session.db,
                    username,
                    password
                )
            except :
                uid = None
            if uid:
                accept_authorization = True
            else:
                # ambbil semua kemungkin token yang ada
                token_list = [get_bearer_token()]
                header_names = []
                if header_name:
                    if isinstance(header_name, str):
                        header_names = [header_name]
                    elif isinstance(header_name, (list, tuple)):
                        header_names = header_name
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
            if uid or setup_session:
                # Set kembali session sebelumnya
                set_session(save_uid, save_login, session_token)
            return result
        return wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)
