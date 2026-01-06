# -*- coding: utf-8 -*-
# Part of Flectra. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _


class IrModel(models.Model):
    _inherit = 'ir.model'

    @api.model
    def is_read_sync_api(self):

        return True

    def readable_fields(self, fields):
        env = self.env
        model_obj = self.env[self.model]
        if not fields:
            _fields = model_obj._fields
            exclude_fields = []
            exclude_fields.extend(env['mail.thread']._fields.keys())
            exclude_fields.extend(env['mail.activity.mixin']._fields.keys())
            exclude_fields.extend(env['mail.blacklist']._fields.keys())
            fs = model_obj.check_field_access_rights('read', None)
            fields = [name for name in fs if
                      name not in exclude_fields and not name.startswith("message_") and not isinstance(
                          _fields[name].compute, bool)]
        return fields
