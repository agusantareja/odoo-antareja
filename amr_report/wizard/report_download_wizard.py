# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class ReportDownloadWizard(models.TransientModel):
    _name = "report.download.wizard"
    _inherit = 'report.download.mixin'
    _description = "Report Download Wizard"


class ReportDownloadAttachmentWizard(models.TransientModel):
    _name = "report.download.attachment.wizard"
    _inherit = 'report.download.attachment.mixin'
    _description = "Report Download Attachment Wizard"
