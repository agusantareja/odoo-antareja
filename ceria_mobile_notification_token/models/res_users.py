from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    ceria_mobile_token_ids = fields.One2many('ceria.mobile.token.user.approval', 'user_id', string='Token',readonly=1)
