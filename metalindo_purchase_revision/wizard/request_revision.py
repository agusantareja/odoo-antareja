# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class request_revision(models.TransientModel):
    _name = 'request.revision'
    _description = 'Request For Revision'

    reason = fields.Text('Reason')
    purchase_id = fields.Many2one('purchase.order')
    
    def button_save(self):
        # Picking dibatalkan
        for move in self.env['stock.move'].sudo().search([('purchase_line_id', 'in', [l.id for l in self.purchase_id.order_line])]):
            if move.picking_id.state not in ['done', 'cancel'] \
                and move.picking_id.picking_type_id == self.purchase_id.picking_type_id:
                move.picking_id.action_cancel()
        self.purchase_id.write({
            # 'state': 'waiting_revision',
            'previous_revision_reason': self.purchase_id.revision_reason,
            'revision_reason': self.reason,
        })
        self.purchase_id.message_post(body="Request PO Revision, Reason: %s"%self.reason)

        #Purchase revision untuk approval nya dihilangkan, jadi auto approve saja
        # karena approval akan dilakukan ketika submit setelah user melakukan revisi        
        self.purchase_id.button_approve_revision()
        # email = self.env['send_message.email']
        # template = self.env.ref('metalindo_purchase_revision.mail_template_approver_revision')
        # message_wa_template = self.env['ir.config_parameter'].sudo().get_param(
        #     'metalindo_purchase_revision.param_message_wa_revision_request_notification'
        # )
        # link = self.purchase_id.link if self.purchase_id.link else '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s' % (
        #     self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
        #     self.purchase_id.id,
        #     self.purchase_id._name,
        #     self.purchase_id.company_id.id,
        #     self.env.ref('purchase.menu_purchase_root').id
        # )
        # approver_group = self.env.ref('metalindo_purchase_revision.group_purchase_revision_approver')
        # for user in approver_group.users:
        #     message_wa = message_wa_template.replace(
        #         "{requester}", self.purchase_id.user_id.name
        #     ).replace(
        #         "{approver}", user.name
        #     ).replace(
        #         "{no_po}", self.purchase_id.name
        #     ).replace(
        #         "{link}", link
        #     )
        #     email.create({
        #         'receiver'    : user.id,
        #         'template'    : template.id,
        #         'is_send'     : False,
        #         'is_send_wa'  : False,
        #         'message'     : message_wa,
        #         'company_id'  : self.purchase_id.company_id.id,
        #         'model_record': self.purchase_id._name,
        #         'id_record'   : self.purchase_id.id,
        #         'ref'         : self.purchase_id.name
        #     })
        return True
