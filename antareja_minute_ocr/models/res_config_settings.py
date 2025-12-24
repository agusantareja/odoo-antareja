# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attachment_api_ocr_endpoint_url = fields.Char(
        "OCR Server",
        help="Enable minute meeting category",
        config_parameter='antareja_ocr_attachment.api_ocr_endpoint_url',
    )

    module_antareja_minute_ocr_queue = fields.Boolean()


