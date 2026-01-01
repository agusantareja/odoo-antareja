from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_queue_job = fields.Boolean()

    using_queue_for_send_message = fields.Boolean(string="Using queue", config_parameter='using_queue_for_send_message')
