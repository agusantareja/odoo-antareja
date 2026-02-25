# -*- coding: utf-8 -*-

import requests
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import traceback
import logging

_logger = logging.getLogger(__name__)


class ApplicationServerPath(models.Model):
    _inherit = 'application.server.path'
    # _inherit = 'ir.config_parameter.able.mixin'

    def get_application_name(self):
        return self.application_server_auth_id.get_application_name()

    def jsonrpc_call(self, model, method, args, kw=None, db=None, uid=None, password=None):
        return self.application_server_auth_id.jsonrpc_call(
            model, method, args, kw=kw, db=db, uid=uid, password=password
        )

    def get_external_data(self, model_name, domain=None, fields=None, offset=None, limit=None, count=False,
                          object_id=None, context=None):
        record = self.ensure_one()
        return record.application_server_auth_id.get_external_data(
            model_name, domain=domain, fields=fields, offset=offset, limit=limit, count=count,
            object_id=object_id, context=context, path=record.path
        )
