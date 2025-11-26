# -*- coding: utf-8 -*-

from odoo import models, fields, api
from firebase_admin import credentials, initialize_app
import firebase_admin

import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
import json
import os

def detect_string_type(value):
    # 1. Cek apakah string merupakan JSON
    try:
        parsed = json.loads(value)
        return "json", parsed
    except:
        pass

    # 2. Cek apakah merupakan path lokal
    if os.path.exists(value):
        return "path_exists", value

    # 3. Cek apakah formatnya seperti path (meski belum ada)
    if "/" in value or "\\" in value:
        return "path_maybe", value

    # 4. Bukan JSON, bukan path
    return "plain_string", value


class FirebaseConfig(models.Model):
    _name = "firebase.config"
    _description = "Firebase Admin Configuration"
    _rec_name = "name"

    name = fields.Char(default="Firebase Config", required=True)
    service_json = fields.Text("Service Account JSON",default="{}")
    config_type = fields.Selection(
        [('json','JSON'),('path_exists','Path Exists'),('path_maybe','Path Maybe'),('plain_string','Plain String')],
        compute="_compute_config_type"
    )
    last_validation = fields.Datetime(readonly=True)
    state_connection = fields.Boolean("Connection", compute="_compute_state_connection")

    @api.depends('service_json')
    def _compute_config_type(self):
        for rec in self:
            config_type, parsed = detect_string_type(rec.service_json)
            rec.config_type = config_type

    def _compute_state_connection(self):
        for rec in self:
            rec.state_connection= bool(firebase_admin._apps)

    @api.onchange("service_json")
    def _onchange_service_json(self):
        """Auto-validasi + auto-pretty-format saat diedit"""
        if not self.service_json:
            return

        config_type, parsed = detect_string_type(self.service_json)
        if 'json' == config_type:
            self.service_json = json.dumps(parsed, indent=4)  # pretty-format
            self.last_validation = fields.Datetime.now()
        else:
            return {
                "warning": {
                    "title": "Invalid JSON",
                    "message":"Invalid JSON"
                }
            }

    @api.model
    def init(self):
        """Dipanggil setiap Odoo start — ideal untuk init firebase."""
        self._initialize_firebase()

    @api.model
    def _initialize_firebase(self):
        """Load JSON dari database & init firebase_admin."""
        try:
            if not firebase_admin._apps:
                config = self.search([], limit=1)
                if not config or not config.service_json:
                    _logger.warning("Firebase not initialized: No JSON configured.")
                    return
                config_type, data = detect_string_type(config.service_json)
                cred = credentials.Certificate(data)
                initialize_app(cred)
                _logger.info("Firebase initialized successfully.")
            else:
                _logger.info("Firebase already initialized, skipped.")

        except Exception as e:
            _logger.error("Firebase init FAILED: %s", e)

    # -----------------------------------------------------
    # Test Connection Button
    # -----------------------------------------------------
    def action_reconnect_connection(self):

        try:
            config_type, data = detect_string_type(self.service_json)
            cred = credentials.Certificate(data)
            firebase_admin.initialize_app(cred)

            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Firebase Connection Success!',
                    'type': 'rainbow_man',
                }
            }

        except Exception as e:
            raise UserError(e)
