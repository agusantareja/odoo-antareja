# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    antareja_application_name = fields.Char(config_parameter='antareja.application_name')

    module_antareja_integration = fields.Boolean("Application Integration")

    module_antareja_notification = fields.Boolean("Notification")
    module_antareja_notification_whatsapp = fields.Boolean("Notification Whatsapp")
    module_antareja_whatsapp_migration = fields.Boolean("WhatsApp Migration")

    module_antareja_approval_manager = fields.Boolean("Approval Manager")
    module_antareja_approval_hr_employee_hierarchy = fields.Boolean("Employee Approval Hierarchy")
    module_antareja_token = fields.Boolean("JWT Token")

    module_antareja_doa = fields.Boolean("Delegation of Authority (DoA)")

    module_antareja_notification_ceria_mobile_intra = fields.Boolean("Ceria Mobile Mobile Intra")

    module_ceria_mobile_notification = fields.Boolean("Ceria Mobile Notification and Approval Server")
    module_ceria_mobile_notification_test = fields.Boolean("Test Module Ceria Mobile Firebase")
    module_ceria_mobile_notification_token = fields.Boolean("Module Ceria Mobile Token")
