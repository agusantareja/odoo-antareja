# -*- coding: utf-8 -*-

from odoo import fields, models


class CniApprovalTransaction(models.Model):
    _inherit = "cni.approval.transaction"

    po_version_id = fields.Many2one(string='PO Version', comodel_name='po.version')
