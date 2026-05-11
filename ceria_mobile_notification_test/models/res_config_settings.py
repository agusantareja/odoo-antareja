from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ceria_mobile_notification_device_test_token = fields.Char(string='Device Test Token', config_parameter='ceria_mobile_notification.device_test_token')
