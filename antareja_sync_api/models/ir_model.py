# -*- coding: utf-8 -*-

from odoo import api, models

EXCLUDE_MODELS = {
    # Technical
    'ir.model',
    'ir.model.fields',
    'ir.cron',
    'ir.ui.view',
    'ir.actions.act_window',

    # Security
    'res.users',
    'res.groups',
    'res.company',
    'res.config.settings',
    'user.delegation',
    'antareja.token',

    # Messaging
    'mail.message',
    'mail.followers',
    'mail.activity',

    'send_message.email',
    'api.call.retry',
}

EXCLUDE_PREFIXES = (
    'ir.',
    'bus.',
    'base.',
    'mail.',
    'web.',
    'internal.data.',
    'external.data.',
    'application.',
    'approval.',
    'antareja.',
    'notification.'
    'whatsapp.'
)


class IrModel(models.Model):
    _inherit = 'ir.model'

    def excluded_read_sync_api(self):
        return self.model in EXCLUDE_MODELS or self.model.startswith(EXCLUDE_PREFIXES)

    @api.model
    def is_read_sync_api(self):
        return True

    @api.model
    def sudo_read_sync_api(self):
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
