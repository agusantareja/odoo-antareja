import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import image_process

import logging

_logger = logging.getLogger(__name__)

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    snipe_hardware_ids = fields.One2many(
        'snipe.hardware',
        'employee_id'
    )

class SnipeHardware(models.Model):
    _name = "snipe.hardware"
    _inherit = ['snipe.server.mixin']
    _description = "hardware from Snipe-IT"
    application_external_id = fields.Integer()
    assigned_to_id = fields.Many2one("snipe.user", string="Snipe Users")
    employee_id = fields.Many2one("hr.employee", related="assigned_to_id.employee_id", store=True,string="Assigned Employee")
    name = fields.Char()
    image_url = fields.Char("Image")
    image_id = fields.Many2one("snipe.image")
    attachment_id = fields.Many2one(
        'ir.attachment',
        related='image_id.attachment_id'
    )
    image_128 = fields.Image("Image", max_width=128, max_height=128, compute="_compute_image_128", store=False)

    @api.depends('image_id')
    def _compute_image_128(self):
        for rec in self:
            if rec.image_id.attachment_id and rec.image_id.attachment_id.datas:
                # Resize agar sesuai ukuran image_128
                rec.image_128 = image_process(
                    rec.image_id.attachment_id.datas,
                    size=(128, 128),
                    crop=False
                )
            else:
                rec.image_128 = False
    image_datas = fields.Binary(related='attachment_id.datas', string="Image", readonly=True)
    serial = fields.Char()
    category = fields.Char()
    model = fields.Char()
    status = fields.Char()
    checkout_date = fields.Datetime()
    location = fields.Char()
    last_sync_datetime = fields.Datetime()

    def cron_sync_from_snipeit_hardware(self):
        self.sync_from_snipeit()

    @api.model
    def sync_from_snipeit_by_serial(self,serial):
        if self.search([('serial','=',serial)]):
            return
        url = self.get_endpoint_hardware_url()+f"/byserial/{serial}"
        headers = self.get_headers_request()
        response = requests.get(url, headers=headers)

        json = response.json()
        data = json.get("rows", [])

        for item in data:
            self.create_or_update_from_external(item)

    def create_or_update_from_external(self,item):
        input_dict = {
            'last_sync_datetime': fields.Datetime.now(),
        }
        # todo chek bila hanya perlu update saja
        input_dict.update(self.prepare_input_dict(item))
        application_external_id = item.get('id')
        existing = self.search([('application_external_id', '=', application_external_id)])
        if existing:
            existing.write(input_dict)
        else:
            input_dict['application_external_id'] = application_external_id
            existing = self.create([input_dict])[0]
        return existing

    @api.model
    def sync_from_snipeit(self):
        url = self.get_endpoint_hardware_url()
        headers = self.get_headers_request()
        # bila di mungkinan filter berdasarkan last_checkout
        # Hapus data lama
        self.search([('application_external_id','=',False)]).unlink()
        params = {
            'offset':0,
            'sort':'id',
            'order': 'asc'
        }
        offset = 0
        total = 1
        while offset < total:
            params['offset'] = offset
            response = requests.get(url, params=params,headers=headers)
            # ambil last sync datetime
            # todo ambil data last sinc dari config param
            if response.status_code != 200:
                raise UserError(f"Failed to fetch data: {response.status_code} - {response.text}")
            json =response.json()
            data = json.get("rows", [])
            _logger.info("count %s ,  offset %s = total %s ", len(data),offset, total)
            total = json.get("total", 0)
            for item in data:
                offset=offset+1
                self.create_or_update_from_external(item)
        _logger.info("offset %s = total %s", offset, total)

    def prepare_input_dict(self,item):
        def ensure_dict(d):
            return d or {}

        assigned = item.get("assigned_to")
        snipe_user = False
        if assigned :
            snipe_user = self.assigned_to_id.search_or_create(assigned)
        status_label = ensure_dict(item.get("status_label"))

        return{
                "name": item.get("name"),
                "serial": item.get("serial"),
                "image_url": item.get("image", ""),
                "category": ensure_dict(item.get("category")).get("name"),
                "model": ensure_dict(item.get("model")).get("name"),
                "status": "%s %s" % (status_label.get("name",""),status_label.get('status_meta','')) ,
                "checkout_date": ensure_dict(item.get("last_checkout")).get("datetime"),
                "location": ensure_dict(item.get("location")).get("name"),
                "assigned_to_id": snipe_user.id if snipe_user else False,
            }

    def create(self, vals_list):
        for vals in vals_list:
            if 'image_url' in vals and not vals.get('image_id'):
                image_url = vals.get('image_url')
                if image_url:
                    image = self.image_id.search([('url', '=', image_url)], limit=1)
                    if not image:
                        image = self.image_id.create({
                            'name': image_url,
                            'url': image_url,
                            'state': 'ready'
                        })

                    vals['image_id']=image.id


        results = super().create(vals_list)

        return results

    def write(self, vals):
        super().write(vals)
        if 'image_url' in vals:
            self.update_image()

    def update_image(self):
        for res in self:
            if res.image_url and (not res.image_id or res.image_id.url != res.image_url):
                image = self.image_id.search([('url', '=', res.image_url)], limit=1)
                if not image:
                    image = self.image_id.create({
                        'name': res.image_url,
                        'url': res.image_url,
                        'state': 'ready'
                    })
                res.write({'image_id':image.id})


    def api_output_dict(self,with_assigned_to=None):
        """
        Return dict representation for API output with assigned_to enhancement.
        """
        self.ensure_one()

        # Base hardware data
        data = {
            #"id": self.id,
            "name": self.name,
            "serial": self.serial,
            "category": self.category,
            "model": self.model,
            "image_url": self.image_id.get_image_url(),
        }

        # Enhance assigned_to
        if with_assigned_to:
            if self.assigned_to_id:
                data["assigned_to"] = self.assigned_to_id.api_output_dict()
            else:
                data["assigned_to"] = None

        return data
