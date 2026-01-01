from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    antareja_doa_external_app_name = fields.Char(
        string="DOA App Name",
        config_parameter='antareja_doa_client.doa_external_app_name'
    )
    antareja_doa_endpoint_url = fields.Char(
        string="DOA Endpoint",
        config_parameter='antareja_doa_client.doa_endpoint_url'
    )
    antareja_doa_api_token = fields.Char(
        string="DOA Token",
        config_parameter='antareja_doa_client.doa_api_token'
    )
