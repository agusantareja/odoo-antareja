# -*- coding: utf-8 -*-

import logging
import werkzeug
from odoo import models
from odoo.exceptions import AccessDenied
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_auto_login_url(self, url=None, create=True):
        token = self.get_access_token(create=create)
        query = {'token_access': token}
        url = url or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        result = urlparse(url)
        redirect = result.path or ""
        if result.fragment:
            if redirect:
                redirect = f"{redirect}#{result.fragment}"
            else:
                redirect = f"/#{result.fragment}"
        if redirect:
            query['redirect'] = redirect
        query_str = werkzeug.url_encode(query)
        return "%s://%s/web_token_access?%s" % (result.scheme, result.netloc, query_str)

    def get_mobile_access_token(self, create=False):
        return self.get_access_token(create=create)

    def get_access_token(self, create=False):
        return self.env['antareja.token'].get_access_token(user=self, create=create)

    # v16 ada parameter env
    def _check_credentials(self, password, env):
        try:
            # v16 ada paremeter env
            return super(ResUsers, self)._check_credentials(password,env)
        except AccessDenied:
            payload = self.env['antareja.token'].validate(password)
            if not payload or payload.get('uid') != self.env.uid:
                raise
