# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SnipServer(models.AbstractModel):
    _name = 'snipe.server.mixin'
    _description = 'Snipe-IT Server Configuration Mixin'

    def get_token(self):
        """
        Mendapatkan token dari konfigurasi sistem.
        Contoh key: antareja_it_asset.snipe_api_token
        dev-cerindo-antareja
        """
        token = self.env["ir.config_parameter"].sudo().get_param("antareja_it_asset.snipe_api_token")
        if not token:
            raise ValueError("Snipe-IT API token belum diatur di System Parameters.")
        return f"Bearer {token}"

    def get_endpoint_url(self):
        """
        Mendapatkan base URL Snipe-IT dari konfigurasi sistem.
        Contoh key: antareja_it_asset.snipe_endpoint_url
        """
        base_url = self.env["ir.config_parameter"].sudo().get_param("antareja_it_asset.snipe_endpoint_url")
        if not base_url:
            raise ValueError("Snipe-IT Endpoint URL belum diatur di System Parameters.")
        return base_url.rstrip("/") + "/api/v1"

    def get_endpoint_hardware_url(self):
        """
        Endpoint untuk /api/v1/hardware
        """
        return f"{self.get_endpoint_url()}/hardware"

    def get_endpoint_users_url(self):
        """
        Endpoint untuk /hardware
        """
        return f"{self.get_endpoint_url()}/users"


    def get_headers_request(self):
        """
        Header untuk permintaan API
        """
        return {
            "Authorization": self.get_token(),
            "Accept": "application/json"
        }
