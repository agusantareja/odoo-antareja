from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import datetime
import logging
_logger = logging.getLogger(__name__)


class AssignBuyer(models.TransientModel):
    _inherit = 'metalindo_direct_charge.assign_buyer'


    bro_ids = fields.Many2many('recommend.qty', string='BRO')


    def action_done(self):
        res = super().action_done()
        if self.bro_ids:
            for bro in self.bro_ids:
                bro.write({'procurement_user_id': self.buyer_id.id, 'state': 'Ready to Purchase'})
                params_message = self.env["ir.config_parameter"].sudo()\
                    .get_param("metalindo_purchase.params_wa_bro_buyer")
                email = self.env['send_message.email']
                action = self.env.ref('metalindo_purchase.buyer_report_recommended_quantity_purchase_action')
                link = '%s/web#action=%s&model=%s&view_type=list&cids=%s&menu_id=%s'%(
                    self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                    action.id,
                    bro._name,
                    bro.company_id.id,
                    self.env.ref('purchase.menu_purchase_root').id,
                )
                replace_message_wa_to_buyer = params_message.replace("{buyer}", self.buyer_id.name)\
                    .replace("{bro_number}", bro.name)\
                    .replace("{link}", link)
                email.create({
                    'receiver'    : self.buyer_id.id,
                    'template'    : False,
                    'is_send'     : True,
                    'is_send_wa'  : False,
                    'message'     : replace_message_wa_to_buyer,
                    'company_id'  : self.env.company.id,
                    'id_record'   : bro.id,
                    'ref'         : bro.name
                })
        return res
