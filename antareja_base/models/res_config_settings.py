# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    antareja_application_name = fields.Char(config_parameter='antareja.application_name')

    module_antareja_sync_api = fields.Boolean("Sync Service API")
    module_antareja_report = fields.Boolean("Report Store")
    module_antareja_integration = fields.Boolean("Application Integration")

    module_antareja_notification = fields.Boolean("Notification")
    module_antareja_notification_whatsapp = fields.Boolean("Notification Whatsapp")
    module_antareja_whatsapp_migration = fields.Boolean("WhatsApp Migration")

    module_antareja_approval_manager = fields.Boolean("Approval Manager")
    module_antareja_approval_admin_user = fields.Boolean("Ignore Admin User on Approval")
    module_antareja_approval_hr_employee_hierarchy = fields.Boolean("Employee Approval Hierarchy")

    module_antareja_token = fields.Boolean("JWT/Token")
    module_antareja_token_client = fields.Boolean("Client API Token")

    module_antareja_doa = fields.Boolean("Delegation of Authority (DoA)")

    module_antareja_approval_ceria_mobile_intra = fields.Boolean("Ceria Apprval Mobile Intra")
    module_antareja_notification_ceria_mobile_intra = fields.Boolean("Ceria Notification Mobile Intra")
