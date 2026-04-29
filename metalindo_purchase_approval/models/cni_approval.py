# -*- coding: utf-8 -*-

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

class CniApprovalTransaction(models.Model):
    _inherit = "cni.approval.transaction"

    po_version_id = fields.Many2one(string='PO Version', comodel_name='po.version')

    def unlink(self):
        trx_id_update = self.browse()
        for rec in self:
            if rec.po_version_id:
                trx_id_update |= rec
        if trx_id_update:
            trx_id_update.write({'transaction_id':False})
            _logger.info("trx_id_update %s ",str(trx_id_update))
        # yang ada po_version_id tidak di unlink
        return super(CniApprovalTransaction,self - trx_id_update).unlink()