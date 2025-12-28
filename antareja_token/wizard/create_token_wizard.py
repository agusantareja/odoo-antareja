import base64
import json
from odoo import models, fields, api
from odoo.exceptions import UserError


class CreateTokenWizard(models.TransientModel):
    _name = "antareja.create.token.wizard"
    _description = "Create Token Wizard"

    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user, required=True,readonly=True)
    expires_in = fields.Integer(string="Expires In (seconds)", default=3600, required=True)

    def action_create(self):
        access_token = self.env['antareja.token'].create_access_token(self.user_id,10)
        return {
            "type": "ir.actions.act_window",
            "res_model": "antareja.token",
            "res_id": access_token.id,
            "view_mode": "form",
            "target": "current",
        }
