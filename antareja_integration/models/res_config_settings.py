# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_antareja_integration_sync = fields.Boolean("Integration Synchronization")

    module_antareja_integration_app_intra_cerindocorp = fields.Boolean("Integration intra.cerindocorp")
    module_antareja_integration_app_erp_cerindocorp = fields.Boolean("Integration erp.cerindocorp")
    module_antareja_integration_app_hr_cerindocorp = fields.Boolean("Integration hr.cerindocorp")
    module_antareja_integration_app_payroll_cerindocorp = fields.Boolean("Integration payroll.cerindocorp")
