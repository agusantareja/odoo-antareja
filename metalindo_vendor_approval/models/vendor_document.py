# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class VendorDocument(models.Model):
    _inherit = 'vendor.document'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ], default='draft')

    @api.ondelete(at_uninstall=False)
    def _unlink_except_approved_document(self):
        if any(doc.state == 'approved' for doc in self):
            raise UserError("Can't delete a previously approved document!")
