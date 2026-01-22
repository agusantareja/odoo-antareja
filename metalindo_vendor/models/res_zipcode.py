# -*- coding: utf-8 -*-

from odoo import api, models


class Zipcode(models.Model):
    _inherit = ['res.zipcode']

    @staticmethod
    def _onchange_uppercase_field(record, field_name):
        # Make sure the requested field is not empty before uppercasing them
        if record[field_name]:
            record[field_name] = record[field_name].upper()

    @api.onchange('name')
    def _onchange_uppercase_name(self):
        self.__class__._onchange_uppercase_field(self, 'name')
