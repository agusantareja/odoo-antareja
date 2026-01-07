# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mobile_approval_server_auth_id = fields.Many2one(
        'application.server.auth',
        string='Notification Mobile Server Auth',
        config_parameter='antareja_approval_ceria_mobile_intra.mobile_approval_server_auth_id'
    )
    mobile_approval_endpoint = fields.Char(
        config_parameter='antareja_approval_ceria_mobile_intra.mobile_approval_endpoint'
    )
    mobile_approval_token = fields.Char(
        config_parameter='antareja_approval_ceria_mobile_intra.mobile_approval_token'
    )
    module_antareja_approval_ceria_mobile_local = fields.Boolean("Local Ceria Mobile Approval")
