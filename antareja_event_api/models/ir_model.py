# -*- coding: utf-8 -*-

from odoo import api, models

class IrModel(models.Model):
    _inherit = 'ir.model'

    # def excluded_read_sync_api(self):
    #     return self.model in EXCLUDE_MODELS or self.model.startswith(EXCLUDE_PREFIXES)

    def is_read_sync_api(self):
        if self.env['internal.data.event.config'].is_event_sync(self.model):
            return True
        super(IrModel, self).is_read_sync_api()

    @api.model
    def sudo_read_sync_api(self):
        if self.env['internal.data.event.config'].is_sudo_read(self.model):
            return True
        super(IrModel, self).is_read_sync_api()

    def readable_fields(self, fields):
        fields = super(IrModel, self).readable_fields(fields) or {}
        env = self.env
        config = env['internal.data.event.config'].get_config(self.model)
        fields -= set(config.get_fields_exclude())
        return fields

        # model_obj = self.env[self.model]
        # if not fields:
        #     _fields = model_obj._fields
        #     exclude_fields = []
        #     exclude_fields.extend(env['mail.thread']._fields.keys())
        #     exclude_fields.extend(env['mail.activity.mixin']._fields.keys())
        #     exclude_fields.extend(env['mail.blacklist']._fields.keys())
        #     fs = model_obj.check_field_access_rights('read', None)
        #     fields = [name for name in fs if
        #               name not in exclude_fields and not name.startswith("message_") and not isinstance(
        #                   _fields[name].compute, bool)]
        # return super(IrModel, self).readable_fields(fields)
