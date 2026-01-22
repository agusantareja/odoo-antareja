# -*- coding: utf-8 -*-

from odoo import api, models


class Country(models.Model):
    _inherit = ['res.country']

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
        """Uppercase all country names in the database"""
        self.env.cr.execute("""
            UPDATE
                res_country
            SET
                name['en_US'] = to_jsonb(UPPER(jsonb_extract_path_text(name, 'en_US')));
        """)
