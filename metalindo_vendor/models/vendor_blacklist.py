# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, get_lang
from datetime import datetime
from odoo.exceptions import Warning


class VendorBlacklistWizard(models.TransientModel):
    _name = 'vendor.blacklist.wizard'
    _description = 'Vendor Blacklist Wizard'

    blacklist_reason = fields.Text(string="Blacklist Reason")
    vendor_id = fields.Integer(string="Vendor ID")

    def action_blacklist(self):
        vendor = self.env['res.partner'].browse(self.vendor_id)
        vendor.write({
            'state_action': 'blackwait',
            'blacklist_reason': self.blacklist_reason,
            'request_blacklist_by': self.env.uid,
            'request_blacklist_date': datetime.now(),
            })


class VendorWhitelistWizard(models.TransientModel):
    _name = 'vendor.whitelist.wizard'
    _description = 'Vendor Whitelist Wizard'

    whitelist_reason = fields.Text(string="Whitelist Reason")
    vendor_id = fields.Integer(string="Vendor ID")

    def action_whitelist(self):
        vendor = self.env['res.partner'].browse(self.vendor_id)
        vendor.write({
            'state_action': 'whitewait',
            'whitelist_reason': self.whitelist_reason,
            'request_whitelist_by': self.env.uid,
            'request_whitelist_date': datetime.now(),
            })
