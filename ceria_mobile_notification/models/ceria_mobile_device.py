# -*- coding: utf-8 -*-

import logging
import firebase_admin

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CeriaMobileDevice(models.Model):
    _inherit = 'ceria.mobile.device'
    _order = 'last_active desc, id desc'

    active = fields.Boolean(default=True)

    def check_active_token_fcm(self, token=None):
        record = self.browse()
        if token:
            record = self.search([('token_fcm', '=', token)], limit=1)
        elif self:
            record = self.ensure_one()
            token = record.token_fcm
        if not record:
            return False

        self.env["firebase.config"]._initialize_firebase()
        if not firebase_admin._apps:
            return

        active = True
        try:
            message = firebase_admin.messaging.Message(token=token, data={"ping": "test"})
            firebase_admin.messaging.send(message)
        except firebase_admin.messaging.UnregisteredError:
            active = False
        except firebase_admin.messaging.InvalidArgumentError:
            active = False
        except Exception:
            _logger.exception("Unexcpected error when checking FCM token %s:", token)
        if not active:
            record.write({'active':False})
        return active
