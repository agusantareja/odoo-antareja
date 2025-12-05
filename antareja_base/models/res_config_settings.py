# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_antareja_notification = fields.Boolean("Notification")
    module_antareja_notification_ceria_mobile_intra = fields.Boolean("Notification Ceria Mobile Client")
    module_antareja_notification_whatsapp = fields.Boolean("Notification Whatsapp")
    module_antareja_whatsapp_migration = fields.Boolean("WhatsApp Migration")
    module_antareja_doa = fields.Boolean("Delegation of Authority (DoA)")


    module_ceria_mobile_notification = fields.Boolean("Ceria Mobile Notification and Approval Server")
    module_ceria_mobile_notification_test = fields.Boolean("Test Module Ceria Mobile Firebase")