# -*- coding: utf-8 -*-

from odoo import api, models


class CountryState(models.Model):
    _inherit = ['res.country.state']

    @staticmethod
    def _onchange_uppercase_field(record, field_name):
        # Make sure the requested field is not empty before uppercasing them
        if record[field_name]:
            record[field_name] = record[field_name].upper()

    @api.onchange('name')
    def _onchange_uppercase_name(self):
        self.__class__._onchange_uppercase_field(self, 'name')

    @api.model
    def _uppercase_all_names(self):
        """Uppercase all state names in the database"""
        self.env.cr.execute("UPDATE res_country_state SET name = UPPER(name);")
