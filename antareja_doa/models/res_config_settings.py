from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_antareja_doa_activate = fields.Boolean("Activate Doa")
    module_antareja_doa_approval = fields.Boolean("Doa Approval")
    module_antareja_integration_doa = fields.Boolean("Doa Intra Integration")

    module_antareja_doa_notif = fields.Boolean()
    module_antareja_doa_server = fields.Boolean()
    module_antareja_doa_client = fields.Boolean("Doa Client")

    group_doa_internal_user_create = fields.Boolean(
        string='User Create DOA',
        implied_group='antareja_doa.group_doa_internal_user_create',
        help="Allows to user Create DoA "
    )
