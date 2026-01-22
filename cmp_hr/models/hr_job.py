# -*- coding: utf-8 -*-
import json

from odoo import models, api, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class HRJob(models.Model):
    _inherit = 'hr.job'

    group_id = fields.Many2one('res.groups', string='Access Group')


