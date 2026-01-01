from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    antareja_hr_employee_approver_max_level_approver = fields.Integer(
        string="Max Level Approver",
        config_parameter='antareja_approval_hr_employee_hierarchy.max_level_approver'
    )
