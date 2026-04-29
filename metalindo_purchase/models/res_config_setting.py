from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vat_validation = fields.Boolean("VAT Validation",config_parameter='metalindo_purchase.vat_validation')