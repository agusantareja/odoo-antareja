# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CniAdditionDeletionRevision(models.Model):
    _name = 'addition.deletion.revision'
    _inherit = [_name, 'cni.approval.transaction.task.able.mixin']

    current_approval_id = fields.Many2one('cni.approval.transaction')
    current_group_id = fields.Many2one('res.groups',"Approval Group")
    current_approval_user_id = fields.Many2one('res.users',"Approval User")

    def compute_can_edit(self):
        for rec in self:
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='id asc')
            rec.can_edit = approver and approver.can_edit

    def compute_mandatory(self):
        for rec in self:
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='id asc')
            rec.mandatory = approver and approver.mandatory
    

    def _compute_is_approver(self):
        for rec in self:
            user_id = self.env.user.id
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='seq asc')
            if user_id in approver.group_id.users.ids:
                rec.is_approver = True
            else:
                rec.is_approver = False

    def button_request_approval(self):
        rec = self.ensure_one()
        rec.action_request_approval()

    def event_approval_start(self,**kwargs):
        trx_update = {
            'adr_status': 'waiting',
            'current_approval_id': False,
            'current_group_id':False,
            'current_approval_user_id':False
            # 'flag_reject': False
        }
        current_approval = kwargs.get('approval_transaction') or self.get_next_approval_task_line()
        if current_approval:
            trx_update['current_approval_id']=current_approval.id
            groups = current_approval.get_groups()
            if groups :
                trx_update['current_group_id'] = groups.ids[0]
            users = self.get_users_approval_notification(**kwargs) or current_approval.get_users()
            if users :
                trx_update['current_approval_user_id'] = users.ids[0]


        self.write(trx_update)
        
    def button_approve_approval(self):
        rec = self.ensure_one()
        rec.action_approve()

    # def event_before_approve(self,approval_transaction=None):
    #     self.check_mandatory()
    #     # FINALIZE CATALOGER
    #     trx = self.ensure_one()
    #     approval_lines_ids = approval_transaction
    #     inventory_cataloguer = self.env.ref('metalindo_inventory.group_metalindo_inventory_cataloger').id
    #     if approval_lines_ids.group_id.id == inventory_cataloguer:
    #         if trx.req_type != 'del':
    #             trx.write({
    #                 'finalized_by': self.env.uid,
    #                 'finalized_date': fields.Date.context_today(self),
    #                 # 'adr_status': 'final'
    #             })
    #         else:
    #             trx.write({
    #                 'done_by': self.env.uid,
    #                 'done_date': fields.Date.context_today(self),
    #                 # 'adr_status': 'done'
    #             })
    #
    #     # SPV CATALOGER STOCK ITEM
    #     inventory_spv_cataloguer = self.env.ref('metalindo_inventory.group_metalindo_inventory_spv_cataloguer').id
    #     if approval_lines_ids.group_id.id == inventory_spv_cataloguer:
    #         trx.sudo()._add_del_rev()
    #
    #     # OFFICER EXIM INPUT HSCODE
    #     inventory_officer_exim = self.env.ref('metalindo_inventory.group_metalindo_officer_exim').id
    #     if approval_lines_ids.group_id.id == inventory_officer_exim:
    #         for line in trx.line_ids:
    #             if not line.product_hscode_id:
    #                 raise ValidationError('HS Code "%s" harus diisi!' % (line.name or line.standard_name))
    #             line.product_template_id.sudo().write({
    #                 'product_hscode_id': line.product_hscode_id.id,
    #             })
    #             # if not line.purchase_category_id:
    #             #     raise ValidationError('Purchase Category "%s" harus diisi'%(line.name or line.standard_name))
    #         trx.write({
    #             'done_by': self.env.uid,
    #             'done_date': fields.Date.context_today(self),
    #             # 'adr_status': 'done'
    #         })

    def event_after_approve(self,**kwargs):
        trx_update = {
            'current_approval_id': False,
            'current_group_id': False,
            'current_approval_user_id': False
            # 'flag_reject': False
        }
        # current_approval = self.get_next_approval_transaction()
        current_approval = kwargs.get('next_approval_transaction')
        if current_approval:
            trx_update['current_approval_id'] = current_approval.id
            groups = current_approval.get_groups()
            if groups:
                trx_update['current_group_id'] = groups.ids[0]
            users = self.get_users_approval_notification(**kwargs) or current_approval.get_users()
            if users:
                trx_update['current_approval_user_id'] = users.ids[0]
        self.write(trx_update)

    def event_before_reject(self):
        pass

    def event_after_reject(self,next_approval_transaction=None):
        self.current_approval_id =next_approval_transaction

    def event_approval_done(self,is_approved=None):
        #if approval_sts == 0:
        if is_approved:
            self.write({
                'approved_by': self.approved_by or self.env.uid,
                'approved_date': self.approved_date or fields.Date.context_today(self),
                'done_by': None,
                'done_date': None,
                'adr_status': 'done'
            })

    # def _filter_todo(self, operator, value):
    #     """Search untuk user yang belum approve"""
    #     # user_id = self.env.user.id
    #     # if user_id in [1, 2]:
    #     #     return []
    #
    #     ids = []
    #     is_cataloger = self.user_has_groups('metalindo_inventory.group_metalindo_inventory_cataloger')
    #     inventory_cataloger = self.env.ref('metalindo_inventory.group_metalindo_inventory_cataloger').id
    #
    #     is_spv_cataloguer = self.user_has_groups('metalindo_inventory.group_metalindo_inventory_spv_cataloguer')
    #     inventory_spv_cataloguer = self.env.ref('metalindo_inventory.group_metalindo_inventory_spv_cataloguer').id
    #
    #     is_officer_exim = self.user_has_groups('metalindo_inventory.group_metalindo_officer_exim')
    #     inventory_officer_exim = self.env.ref('metalindo_inventory.group_metalindo_officer_exim').id
    #
    #     adrs = self.env['addition.deletion.revision'].sudo().search([('adr_status', '!=', 'done')])
    #     for adr in adrs:
    #         approvals = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', adr.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='seq asc')
    #         if is_cataloger or is_spv_cataloguer or is_officer_exim:
    #             if self._uid in approvals.group_id.users.ids:
    #                 if approvals.group_id.id == inventory_cataloger:
    #                     ids.append(approvals.transaction_id)
    #                 elif approvals.group_id.id == inventory_spv_cataloguer:
    #                     ids.append(approvals.transaction_id)
    #                 elif approvals.group_id.id == inventory_officer_exim:
    #                     ids.append(approvals.transaction_id)
    #         else:
    #             ids.append(adr.id)
    #     return [('id', 'in', ids)]

    def get_users_approval_notification(self, **kwargs):
        rec = self.ensure_one()
        analytic = rec.analytic_id
        approval_transaction =  kwargs.get('next_approval_transaction') or kwargs.get('approval_transaction') or  rec.current_approval_id or rec.get_next_approval_task_line()
        users_candidate = approval_transaction.get_users_approval_notification(**kwargs)
        users = self.env['res.users']
        for user in users_candidate:
            if user.id in [1, 2] or user.admin_user:
                continue
            if not approval_transaction.skip_cost_center_check and analytic.id not in user.account_analytic_ids.ids:
                continue
            users |= user
        return  users

    # def compute_approver_group(self):
    #     """Compute untuk alert approver"""
    #     for rec in self:
    #         approver_name = ""
    #         list_approver = []
    #         approver_user = ""
    #         param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.alert_waiting_approval')
    #         approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='id asc')
    #         if approver:
    #             approver_name = approver.group_id.display_name
    #             if approver.group_id.users:
    #                 for user in approver.group_id.users:
    #                     if user.id in [1, 2] or user.admin_user:
    #                         continue
    #                     if (not approver.skip_cost_center_check) and (rec.analytic_id.id not in user.account_analytic_ids.ids):
    #                         continue
    #                     list_approver.append(user.name)
    #         if list_approver:
    #             approver_user = " / ".join(list_approver)
    #             approver_name = approver_name+" ( "+approver_user+" ) "
    #         alert = param.replace("{approver}", str(approver_name))
    #         rec.alert_waiting_approval = alert

