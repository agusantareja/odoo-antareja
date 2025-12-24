from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    snipe_endpoint_url = fields.Char(string="Snipe Endpoint",  config_parameter='antareja_it_asset.snipe_endpoint_url')
    snipe_api_token = fields.Char(string="Snipe Token", config_parameter='antareja_it_asset.snipe_api_token')
