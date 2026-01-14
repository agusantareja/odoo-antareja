
from odoo import models


class DataEventMixin(models.AbstractModel):
    _inherit = 'base'

    def _event_light_log_create(self, record):
        # safety
        if self.env.context.get('skip_data_event'):
            return

        # exclude audit models
        if self._name in {
            'internal.data.event',
            'internal.data.event.config',
        }:
            return

        config = self.env['internal.data.event.config'].sudo().get_config_write(self._name)

        if not config:
            return

        AuditEvent = self.env['internal.data.event'].sudo()
        for rec in record:
            AuditEvent.create({
                'res_model': rec._name,
                'res_id': rec.id,
                'operation': 'write',
                'changed_fields': "",
            })

    def _event_light_log_write(self, vals):
        # safety
        if self.env.context.get('skip_audit'):
            return

        # exclude audit models
        if self._name in {
            'internal.data.event',
            'internal.data.event.config',
        }:
            return

        config = self.env['internal.data.event.config'].sudo().get_config_write(self._name)

        if not config:
            return

        changed = set(vals.keys()) - {
            'write_uid', 'write_date', '__last_update'
        } & config.get_fields_monitor()

        if not changed:
            return

        AuditEvent = self.env['internal.data.event'].sudo()
        for rec in self:
            AuditEvent.create({
                'res_model': rec._name,
                'res_id': rec.id,
                'operation': 'write',
                'changed_fields': ",".join(changed),
            })

    def _event_light_log_unlink(self):
        # safety
        if self.env.context.get('skip_audit'):
            return

        # exclude audit models
        if self._name in {
            'internal.data.event',
            'internal.data.event.config',
        }:
            return

        config = self.env['internal.data.event.config'].sudo().get_config_write(self._name)

        if not config:
            return

        AuditEvent = self.env['internal.data.event'].sudo()
        for rec in self:
            AuditEvent.create({
                'res_model': rec._name,
                'res_id': rec.id,
                'operation': 'write',
                'changed_fields': "",
            })
