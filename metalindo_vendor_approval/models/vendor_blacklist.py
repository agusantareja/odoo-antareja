# -*- coding: utf-8 -*-
from odoo import fields, models, _
from datetime import datetime


class VendorBlacklistWizard(models.TransientModel):
    _name = 'vendor.blacklist.wizard'
    _description = 'Vendor Blacklist Wizard'

    blacklist_reason = fields.Text(string="Blacklist Reason")
    vendor_id = fields.Integer(string="Vendor ID")
    supplier_blacklisted = fields.Boolean(
        ompute='_compute_supplier_blacklisted',
        help="""Readonly untuk field khusus vendor (supplier) """
    )
    def _compute_supplier_blacklisted(self):
        for record in self:
            record.supplier_blacklisted = record.state =='blacklisted'


    def action_blacklist(self):
        vendor = self.env['res.partner'].browse(self.vendor_id)
        vendor.approval_ids = False
        vendor.env['cni.matrix.approval.line'].request_by_value(
            vendor,
            0,
            False,
            'vendor approval'
        )
        vendor.write({
            'approval_type': 'blacklist',
            'state': 'waiting',
            'flag_reject': False,
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
        vendor.approval_ids = False
        vendor.env['cni.matrix.approval.line'].request_by_value(
            vendor,
            0,
            False,
            'vendor approval'
        )
        vendor.write({
            'approval_type': 'whitelist',
            'state': 'waiting',
            'flag_reject': False,
            'whitelist_reason': self.whitelist_reason,
            'request_whitelist_by': self.env.uid,
            'request_whitelist_date': datetime.now(),
        })


class VendorChangeWizard(models.TransientModel):
    _name = 'vendor.change.wizard'
    _description = 'Vendor Change Wizard'

    change_reason = fields.Text(string="Change Reason")
    vendor_id = fields.Integer(string="Vendor ID")

    def action_change(self):
        vendor = self.env['res.partner'].browse(self.vendor_id)
        vendor.write({
            'approval_type': 'change',
            'state': 'draft',
            'flag_reject': False,
            'change_reason': self.change_reason,
            'request_change_by': self.env.uid,
            'request_change_date': datetime.now(),
        })
