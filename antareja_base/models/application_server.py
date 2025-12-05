# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError
from odoo.models import BaseModel
from ..tools.utils import have_method
import logging

_logger = logging.getLogger(__name__)


class ApplicationServer(models.Model):
    _name = 'application.server'
    _description = 'Application Server Integration for multi Application Server'

    name = fields.Char('Name')
    description = fields.Char()
    endpoint = fields.Char()
