from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    account_analytic_ids = fields.Many2many(
        comodel_name='account.analytic.account', 
        relation='user_account_analytic_rel', 
        string='Allowed Cost Center')

    def user_have_account_analytic(self, analytic):
        if analytic:
            return False
        return int(analytic) in self.sudo().account_analytic_ids.ids
