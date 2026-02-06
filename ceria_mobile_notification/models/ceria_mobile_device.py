# -*- coding: utf-8 -*-

import logging
import firebase_admin

from odoo import models, fields, api
from firebase_admin import messaging

_logger = logging.getLogger(__name__)

class CeriaMobileDevice(models.Model):
    _inherit = 'ceria.mobile.device'
    _order = 'last_active desc, id desc'

    active = fields.Boolean(default=True)

    def check_activate_token_fcm(self,token=None):
        if token:
            record=self.search([('token_fcm','=',token)],limit=1)
        elif self:
            record=self.ensure_one()
        else:
            record=self.browse()

        if not record:
            return False
        self.env["firebase.config"]._initialize_firebase()
        if not firebase_admin._apps:
            return
        try:
            message = messaging.Message(
                token=token,
                data={"ping": "test"}
            )
            messaging.send(message)
            active=True
        except messaging.UnregisteredError:
            active=False
        except messaging.InvalidArgumentError:
            active=False
        except Exception as e:
            _logger.error("Error lain: %s", e)
            active=True

        if not active:
            record.write({'active':False})
        return active