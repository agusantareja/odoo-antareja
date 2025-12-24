from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import requests


class SnipeImage(models.Model):
    _name = "snipe.image"
    _description = "Image from Snipe-IT"

    name = fields.Char('Name',required=True)
    state = fields.Selection(
        [('draft','Draft'),
         ('ready','Ready'),
         ('cron', 'Cron'),
         ('queue','Queue'),
         ('done','done'),
         ('fail','Fail'),
         ]
    )
    error_response = fields.Text()
    mimetype = fields.Char(readonly=True)
    file_size = fields.Integer(readonly=True)  # dalam byte
    url = fields.Char('URL', required=True)

    @api.constrains('url')
    def _check_url(self):
        for rec in self:
            if not rec.url.startswith(('http://', 'https://')):
                raise ValidationError("URL harus diawali dengan http:// atau https://")

    attachment_id = fields.Many2one(
        'ir.attachment',
        string="Attachment",
        ondelete='cascade'
    )

    def cron_download(self):
        result = self.sudo().search([('state','=','ready')])
        result.write({'state': 'cron'})
        result._download()

    def action_download(self):
        self._download()

    def _download(self):
        for rec in self:
            try:
                attachment = rec._download_image()
                rec.write({
                    'attachment_id': attachment.id,
                    'mimetype': attachment.mimetype,
                    'file_size': attachment.file_size,
                    'state': 'done',
                })
            except Exception as e:
                rec.write({
                    'state': 'fail',
                    'error_response': str(e),
                })

    def _download_image(self):
        import base64, requests
        from PIL import Image
        import io
        response = requests.get(self.url, timeout=10)
        response.raise_for_status()
        # 1. Validasi Content-Type
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"URL bukan file gambar. Content-Type: {content_type}")

        # 2. Validasi dengan Pillow
        try:
            img = Image.open(io.BytesIO(response.content))
            img.verify()
        except Exception:
            raise ValueError("File tidak valid atau bukan gambar")

        # 3. Validasi ukuran
        if len(response.content) > 10 * 1024 * 1024:
            raise ValueError("Ukuran file terlalu besar")

        # 4. Simpan ke attachment
        encoded = base64.b64encode(response.content)
        return self.env['ir.attachment'].create({
            'name': self.url.split('/')[-1] or 'image.jpg',
            'datas': encoded,
            'mimetype': response.headers.get('Content-Type'),
            'res_model': self._name,
            'res_id': self.id,
            "public": True
        })

    def get_image_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if self.attachment_id:
            return base_url+f"/web/content/{self.attachment_id.id}"
        else:
            return None
