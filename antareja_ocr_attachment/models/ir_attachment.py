# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json

from odoo import api, models, fields
import requests
import base64
import logging

_logger = logging.getLogger(__name__)


class Attachment(models.Model):

    _inherit = "ir.attachment"

    ocr_extracted_text = fields.Text(string="OCR Text", help="The text extracted from the pdf using OCR.")
    ocr_status = fields.Selection(
        [('not_extracted', 'Not Extracted'),
         ('extracted', 'Extracted'),
         ('data_empty', 'Data Empty'),
         ('can_not_extracted', 'Can Not Extracted'),
         ],
        string='OCR Status',
        default='not_extracted',
        help="Status of the OCR extraction process."
    )

    def get_extract_able(self):
        self.ensure_one()
        return self.mimetype == 'application/pdf'

    def get_api_ocr_endpoint_url(self):
        return self.env['ir.config_parameter'].get_param('antareja_ocr_attachment.api_ocr_endpoint_url')

    def call_ocr_extract_text(self, force_extracted=False):
        """ Call the OCR API to extract text from the attachment's PDF file. """
        if not self.ids:
            return self.browse()

        data_list= []
        for rec in self:
            if not (rec.get_extract_able()):
                rec.ocr_status= 'can_not_extracted'
                continue
            if rec.ocr_status == 'extracted' and not force_extracted:
                continue

            if not rec.datas:
                rec.ocr_extracted_text = ''
                _logger.info("Attachment %s tidak dapat diekstrak karena data kosong", rec.name)
                rec.ocr_status = 'data_empty'
                continue

            base64_string = rec.datas.decode("utf-8")

            data = {
                'refId': rec.id,
                'name': rec.name,
                'mimeType': rec.mimetype,
                'data': base64_string,
            }
            data_list.append(data)

        if not data_list:
            return self.browse()

        # Call the OCR API

        json_data = json.dumps(data_list)
        response = requests.post(
            url=self.get_api_ocr_endpoint_url(),
            json=json_data,
        )
        response.raise_for_status()
        _logger.info("Request was successful")
        try:
            data_response_list = response.json()
        except json.JSONDecodeError as json_err:
            _logger.error("JSON Decode Error: %s\n%s", json_err, response.text)
            _logger.info("JSON Request: %s", json_data)
            raise json_err

        update_records_ids = []
        for data_response in data_response_list:
            ref_id = int(data_response['refId'])
            record = self.filtered(lambda d: d.id == ref_id)
            record.write({
                'ocr_status': 'extracted',
                'ocr_extracted_text' : data_response.get('output', ''),
            })
            update_records_ids.append(ref_id)
        return self.browse(update_records_ids)


