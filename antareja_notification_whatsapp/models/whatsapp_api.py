# -*- coding: utf-8 -*-

import logging
import ast

from odoo import models, fields

_logger = logging.getLogger(__name__)


class WhatsappApi(models.Model):
    _inherit = 'whatsapp.api'

    credential_id = fields.Many2one('service.credential')

    def get_request_headers(self):
        try:
            headers = ast.literal_eval(self.whatsapp_api_id.header)
        except Exception as e:
            _logger.error("Error parsing headers for WhatsApp API ID %s: %s", self.whatsapp_api_id.id, e)
            headers = {}
        if self.credential_id:
            provider = self.get_provider()
            headers_context =provider.authenticate({'headers':headers or {}})
            headers=headers_context['headers']
            _logger.info("keys whatsapp.api headers %s .",headers.keys())

        return headers


    def get_provider(self):
        loader = self.env["service.credential.loader"]
        credential_data = loader.load_credential(self.credential_id)
        return self.env["service.auth.factory"].create_service_auth(credential_data)

