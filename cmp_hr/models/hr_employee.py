# -*- coding: utf-8 -*-
import json

from odoo import models, api, fields, _, Command
from odoo.tools.misc import format_date

class HREmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    nip = fields.Char('NIP')
    bank_name = fields.Char(string='Bank Name')
    nama_rekening = fields.Char(string='Account Name')
    no_rekening = fields.Char(string='Account No')
    acting = fields.Boolean('Acting')
    job_position = fields.Char('Job Position', compute='_compute_acting', compute_sudo=True)

    def _compute_acting(self):
        for rec in self:
            if rec.acting and rec.job_id:
                rec.job_position = '[Acting] ' + rec.job_id.name
            elif rec.job_id:
                rec.job_position = rec.job_id.name
            else:
                rec.job_position = ''
