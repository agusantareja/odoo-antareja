from odoo import api, fields, models, _


class MaterialInventoryRequest(models.Model):
    _inherit = 'material.inventory.request'

    def _picking(self):
        super(MaterialInventoryRequest. self)._picking()
        if self.request_type == 'issue':
            self._recommending_qty()

