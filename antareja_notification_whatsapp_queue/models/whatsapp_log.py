# -*- coding: utf-8 -*-

from odoo import models

class WhatsAppLog(models.Model):
    _inherit = 'whatsapp.log'

    def dispatch_send(self):
        self.with_delay().send()

