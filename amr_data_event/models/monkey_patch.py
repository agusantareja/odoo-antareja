from odoo.models import BaseModel
from odoo import api
import logging

_logger = logging.getLogger(__name__)

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
    'user.delegate',
    'antareja.token',

    # Messaging
    'mail.message',
    'mail.followers',
    'mail.activity',

    #
    'external.data.event',
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
    'user.delegate.'
    'whatsapp.'
)

# simpan reference original method
_original_create = BaseModel.create
_original_write = BaseModel.write
_original_unlink = BaseModel.unlink


def is_excluded(model_name):
    return model_name in EXCLUDE_MODELS or model_name.startswith(EXCLUDE_PREFIXES)


@api.model_create_multi
def event_create(self, vals_list):
    records = _original_create(self, vals_list)

    try:
        records and is_excluded(self._name) or self._event_light_log_create(records)
    except Exception:
        _logger.exception("Audit create failed")

    return records


def event_write(self, vals):
    result = _original_write(self, vals)
    try:
        self and is_excluded(self._name) or self._event_light_log_write(vals)
    except Exception:
        _logger.exception("Audit write failed")

    return result


def event_unlink(self):
    try:
        self and is_excluded(self._name) or self._event_light_log_unlink()
    except Exception:
        _logger.exception("Audit unlink failed")

    return _original_unlink(self)


BaseModel.create = event_create
BaseModel.write = event_write
BaseModel.unlink = event_unlink
