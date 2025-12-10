# -*- coding: utf-8 -*-

import logging
import werkzeug
from odoo import http, fields, SUPERUSER_ID, _
from odoo.http import request
from werkzeug import url_encode

_logger = logging.getLogger(__name__)


class ControllerMobileAccess(http.Controller):

    @http.route(['/web_mobile_access',], type='http', auth='none', methods=['GET'], csrf=False)
    def web_mobile_access(self, mobile_token=None, **kw):

        if request.session.uid:
            _logger.info("Sudah login")
        else:
            user = request.env['mobile.access.token'].get_user(mobile_token)
            user and request.session.authenticate(request.session.db, uid=user.id, password=mobile_token)
            #return http.redirect_with_hash('/web')
        if kw:
            url = "/web#%s"% url_encode(kw)
        else:
            url = "/web"
        return werkzeug.utils.redirect(url)

