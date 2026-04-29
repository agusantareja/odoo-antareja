# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class vendor_code(models.Model):
    _inherit = 'vendor.code'

    impor_domestik = fields.Selection([
        ('impor', 'Impor'),
        ('domestik', 'Domestik'),
        ], 'Impor/Domestik')
