# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VendorDocument(models.Model):
    _name = "vendor.document"
    _description = 'Vendor Document'

    still_valid = fields.Boolean(default=True, string='Still Valid?')
    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        domain=[('supplier_rank', '>', 0), ('is_company', '=', True)]
    )
    type = fields.Selection([
        ('surat_nib', 'Surat NIB'),
        ('surat_pkp','Surat Keterangan PKP'),
        ('surat_non_pkp','Surat Keterangan Non-PKP'),
        ('kartu_npwp', 'Kartu NPWP'),
        ('akta_pendirian','Akta Pendirian Perusahaan'),
        ('akta_perubahan', 'Akta Perubahan Perusahaan'),
        ('surat_domisili', 'Surat Keterangan Domisili Perusahaan'),
        ('laporan_keuangan', 'Laporan Keuangan 2 Tahun Terakhir'),
        ('sertifikat_tkdn', 'Sertifikat TKDN'),
        ('bukti_sertifikasi', 'Bukti-Bukti Sertifikasi'),
    ], required=False)
    type_id = fields.Many2one('vendor.document.type', string='Type')
    attachment_ids = fields.Many2many('ir.attachment', string='Files', required=True)
    notes = fields.Text()

    # This is for fixing a bug, see:
    # https://github.com/odoo/odoo/pull/82111
    @api.model
    def create(self, values):
        result = super().create(values)

        # fix attachment ownership
        if result.attachment_ids:
            result.attachment_ids.write({'res_model': self._name, 'res_id': result.id})

        return result





class VendorDocumentType(models.Model):
    _name = "vendor.document.type"
    _description = 'Vendor Document Type'


    name = fields.Char(string='Name')