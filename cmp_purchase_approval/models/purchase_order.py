# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, get_lang
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.http import request, route
from odoo import http
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = [_name, 'cni.approval.transaction.task.able.mixin']
    approval_ids = fields.One2many('cni.approval.transaction', 'transaction_id', string="Approval", domain=[('form_id','=','purchase.order')])
    approval_state = fields.Selection([
        ('b','Belum Request'),
        ('rf','Request For Approval'),
        ('a','Approved'),
        ('r','Rejected')
        ], 'Approval State', readonly=True, default='b')
    is_sent_email_approval = fields.Boolean(default=False)
    email_penerima_approval = fields.Char('Email Penerima')
    exclusive = fields.Selection(related='requisition_id.type_id.exclusive')
    requisition_state = fields.Selection(related='requisition_id.state')
    is_approver = fields.Boolean(related='access_approval')

    # alert form
    alert_waiting_approval = fields.Text(string="Alert waiting approval", compute="compute_approver_group")
    flag_reject = fields.Boolean(string="Flag Reject")
    note_reject = fields.Text(string="Note Reject")
    link = fields.Text(string='Link', copy=False)


    # def _compute_is_approver(self):
    #     for rec in self:
    #         rec.is_approver = rec.access_approval
            # user_id = self.env.user.id
            # approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'purchase order')], limit=1, order='seq asc')
            # rec.is_approver = if user_id in approver.group_id.users.ids:
            #      True


    def button_submit(self):
        for order in self:
            order.action_request_approval()

    def event_approval_start(self):
        order = self
        order.write({
            'state': 'waiting_for_approval',
            'approval_state': 'rf',
            'flag_reject': False,
        })
        for line in order.order_line:
            line.mr_id.write({
                'mr_status': 'purchased'
            })
        # order.approval_ids = False
        #self.env['cni.matrix.approval.line'].request_by_value(order, order.amount_total, order.currency_id, 'purchase order', order.user_id.id)
        # param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.param_message_approval_purchase_order')
        # approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', order.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'purchase order')], limit=1, order='seq asc')
        # link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s'%(
        #         self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
        #         order.id,
        #         order._name,
        #         order.company_id.id,
        #         self.env.ref('purchase.menu_purchase_root').id
        #     )
        # if order.link:
        #     link = order.link
        # email = self.env['send_message.email']
        # template = self.env.ref('metalindo_approval.purchase_approver_mail_template')
        # if approver:
        #     for user in approver.group_id.users:
        #         if user.id in [1, 2] or user.admin_user:
        #             continue
        #         message_wa = param.replace("{approver}", user.name).replace("{no_po}", order.name).replace("{link}", link)
        #         email.create({
        #         'receiver'    : user.id,
        #         'template'    : template.id,
        #         'is_send'     : False,
        #         'is_send_wa'  : False,
        #         'message'     : message_wa,
        #         'company_id'  : order.company_id.id,
        #         'id_record'   : order.id,
        #         'ref'         : order.name
        #     })

    # def event_before_approve(self,approval_task_line):

    #     self.send_notif_to_buyer()
    #
    # def send_notif_to_buyer(self):
        approver=approval_task_line


        # approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', self.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'purchase order')], limit=1, order='seq asc')

        # link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s' % (
        #     self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
        #     self.id,
        #     self._name,
        #     self.company_id.id,
        #     self.env.ref('purchase.menu_purchase_root').id
        # )
        #Jika Approval adalah SCM MANAGER maka akan memberitahu notifikasi WA saja ke buyer bahwa sudah fully approved
        #grup scm manager tidak bisa di search by xml id karena sepertinya create manual grupnya
        # group_category_scm = self.env.ref('metalindo_inventory.module_category_metalindo_inventory')
        # group_scm_manager = self.env['res.groups'].sudo().search([('category_id', '=', group_category_scm.sudo().id), ('name', '=', 'Manager')])
        # if group_scm_manager and approver.get_groups() & group_scm_manager:
        #     notification_template_buyer = self.env.ref('cmp_purchase_approval.notification_template_buyer')
        #     users = approver.get_users()
        #     notification_template_buyer.send_notification_to_users(users,self.id)
            # param_message_wa_to_buyer = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.param_message_approval_purchase_order_to_buyer')
            # email = self.env['send_message.email']
            # replace_message_wa_to_buyer = param_message_wa_to_buyer.replace("{buyer}", self.user_id.name).replace("{no_po}", self.name).replace("{link}", link)
            # email.create({
            #     'receiver'    : self.user_id.id,
            #     'template'    : False,
            #     'is_send'     : True,
            #     'is_send_wa'  : False,
            #     'message'     : replace_message_wa_to_buyer,
            #     'company_id'  : self.company_id.id,
            #     'id_record'   : self.id,
            #     'ref'         : self.name
            # })

    def button_approve_approval(self):
        rec = self.ensure_one()
        rec.action_approve()
        # NEW CODE
        # self.send_notif_to_buyer()
        # approval_sts = self.env['cni.matrix.approval.line'].approve(self)

    def event_approval_done(self, is_approved=False):
        # if approval_sts == 0:
        if is_approved:
            self.button_confirm()
            for pr in self.order_line.mr_id:
                pr.check_state_done()
        # else:
        #     param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.param_message_approval_purchase_order')
        #     approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', self.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'purchase order')], limit=1, order='seq asc')
        #     link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s' % (
        #         self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
        #         self.id,
        #         self._name,
        #         self.company_id.id,
        #         self.env.ref('purchase.menu_purchase_root').id
        #     )
        #     if self.link:
        #         link = self.link
        #     email = self.env['send_message.email']
        #     template = self.env.ref('metalindo_approval.purchase_approver_mail_template')
        #     if approver:
        #         for user in approver.group_id.users:
        #             message_wa = param.replace("{approver}", user.name).replace("{no_po}", self.name).replace("{link}", link)
        #             email.create({
        #                 'receiver'    : user.id,
        #                 'template'    : template.id,
        #                 'is_send'     : False,
        #                 'is_send_wa'  : False,
        #                 'message'     : message_wa,
        #                 'company_id'  : self.company_id.id,
        #                 'id_record'   : self.id,
        #                 'ref'         : self.name
        #             })
        #
        # return approval_sts

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            if order.state not in ('purchase', 'done'):
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step'\
                        or (order.company_id.po_double_validation == 'two_step'\
                            and order.amount_total < self.env.company.currency_id._convert(
                                order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                        or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
        return True
    

    def compute_approver_group(self):
        """Compute untuk alert approver"""
        for rec in self:
            approver_name = ""
            list_approver = []
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'purchase order')], limit=1, order='seq asc')
            if approver:
                approver_name = approver.group_id.display_name
                if approver.group_id.users:
                    for user in approver.group_id.users:
                        if user.id in [1, 2] or user.admin_user:
                            continue

                        list_approver.append(user.name)
            if list_approver:
                approver_user = " / ".join(list_approver)
                approver_name = approver_name+" ( "+approver_user+" )"

            param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.alert_waiting_approval')
            alert = param.replace("{approver}", str(approver_name))
            rec.alert_waiting_approval = alert

    @api.model
    def create(self,vals):
        result = super(PurchaseOrder, self).create(vals)
        # link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s'%(
        #             self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
        #             result.id,
        #             self._name,
        #             result.company_id.id,
        #             self.env.ref('purchase.menu_purchase_root').id
        #         )
        result.link = result.get_internal_url()
        return result

    def get_internal_menu_id(self):
        return self.env.ref('purchase.menu_purchase_root').id