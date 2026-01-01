# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SnipServer(models.AbstractModel):
    _name = 'doa.server.mixin'
    _description = 'Server Configuration Mixin'

    def get_token(self):
        token = self.env["ir.config_parameter"].sudo().get_param("antareja_doa_client.doa_api_token")
        if not token:
            raise ValueError("API token belum diatur di System Parameters.")
        return token

    def get_endpoint_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("antareja_doa_client.doa_endpoint_url")
        if not base_url:
            raise ValueError("DOA Endpoint URL belum diatur di System Parameters.")
        return base_url.rstrip("/") + "/api/sync/data"

    def get_doa_app_name(self):
        return self.env["ir.config_parameter"].sudo().get_param("antareja_doa_client.doa_external_app_name",'intra.cerindocorp.id')

    def get_endpoint_user_delegate_url(self):
        return f"{self.get_endpoint_url()}/user_delegate"

    def get_endpoint_model_name_url(self):
        return f"{self.get_endpoint_url()}/{self._name}"

    def get_headers_request(self):
        return {
            "token": self.get_token(),
            "Accept": "application/json"
        }
