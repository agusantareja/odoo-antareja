from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_antareja_doa_approval = fields.Boolean()
    module_antareja_doa_notif = fields.Boolean()
    module_antareja_doa_server = fields.Boolean()
    module_antareja_doa_client = fields.Boolean()
