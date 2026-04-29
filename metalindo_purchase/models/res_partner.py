# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import UserError


class res_partner(models.Model):
    _inherit = 'res.partner'


    def _default_reminder_date_before_receipt(self):
        days = self.env['ir.config_parameter'].get_param('metalindo_purchase.reminder_date_before_receipt')
        return int(days)


    receipt_reminder_email = fields.Boolean('Receipt Reminder', default=True, company_dependent=True,
        help="Automatically send a confirmation email to the vendor X days before the expected receipt date, asking him to confirm the exact date.")
    reminder_date_before_receipt = fields.Integer('Days Before Receipt', default=_default_reminder_date_before_receipt, company_dependent=True,
        help="Number of days to send reminder email before the promised receipt date")
    is_delivery_point = fields.Boolean('Delivery Point')
    delivery_point_name = fields.Char('Delivery Point Name', compute="_compute_delivery_point_name")
    picking_type_id = fields.Many2one('stock.picking.type', 'Stock Operation Type')


    def get_address_str(self):
        address_field = [
            self.street,
            self.street2,
            self.city,
            self.state_id.name,
            self.zip,
            self.country_id.name
        ]
        return ', '.join([x for x in address_field if x])

    @api.constrains('id','vat')
    def check_vat(self):
        vat_validation = self.env['ir.config_parameter'].search([('key','=','metalindo_purchase.vat_validation')])
        if vat_validation and vat_validation.value == 'True':
            for rec in self:
                if rec.is_company:
                    if not rec.vat:
                        raise UserError('Please fill VAT/NPWP')
                    check_existing = self.search([('vat','=',rec.vat),('id','!=',rec.id)])
                    if check_existing:
                        raise UserError('There is already a Vendor with vat %s'%rec.vat)
                    
    @api.constrains('reminder_date_before_receipt')
    def _constrains_reminder_date_before_receipt(self):
        for rec in self:
            if rec.reminder_date_before_receipt <= 0:
                raise UserError(_("Day(s) before cannot be 0 or less"))

    # @api.constrains('delivery_point_name', 'city')
    # def set_delivery_point_name(self):
    #     for rec in self:
    #         if rec.is_delivery_point:
    #             rec.name = '%s - %s'%(rec.delivery_point_name,rec.city) if rec.city else rec.name

    def _compute_delivery_point_name(self):
        for rec in self:
            if rec.is_delivery_point:
                rec.delivery_point_name = rec.name
