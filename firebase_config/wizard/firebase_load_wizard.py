import base64
import json
from odoo import models, fields, api
from odoo.exceptions import UserError


class FirebaseLoadWizard(models.TransientModel):
    _name = "firebase.load.wizard"
    _description = "Load JSON File Wizard"

    file = fields.Binary("File JSON", required=True)
    filename = fields.Char()

    def action_load(self):
        if not self.file:
            raise UserError("File tidak ditemukan.")

        # Decode base64
        try:
            raw_bytes = base64.b64decode(self.file)
        except Exception:
            raise UserError("File tidak valid base64.")

        # Decode UTF-8 → teks JSON
        try:
            json_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise UserError("File bukan UTF-8.")

        # Validasi JSON
        try:
            json.loads(json_text)
        except json.JSONDecodeError as e:
            raise UserError(f"File JSON tidak valid:\n{str(e)}")

        # Simpan ke config
        config = self.env["firebase.config"].search([], limit=1)
        config.service_json = json_text  # onchange di model config akan pretty-format dll.

        return {
            "type": "ir.actions.act_window",
            "res_model": "firebase.config",
            "res_id": config.id,
            "view_mode": "form",
            "target": "current",
        }
