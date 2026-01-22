# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)

class CniMaterialRequisition(models.Model):
    _name = 'material.requisition'
    _inherit = [_name,'cni.approval.transaction.task.able.mixin']

    todo = fields.Boolean(string='To Do', compute='_compute_todo', search='_filter_todo')

    def action_approval_transaction(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self._description,
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'context':{
                'create': 0,
                'edit': self.is_cost_control,
                'delete': 0
            }
        }

    def _compute_todo(self):
        for rec in self:
            if rec.originator_id == self.env.user:
                rec.todo = True
            else:
                approver = rec.get_next_approval_task_line()
                rec.todo =  approver and self.env.user in approver.get_users()

    def _filter_todo(self, operator, value):
        # cari mr yang dibuat oleh user login dan statusnya belum done
        originator_ids = self.sudo().search([('mr_status', '!=', 'done'), ('originator_id', '=', self.env.user.id)]).ids
        # cari mr yang bukan dibuat oleh user login dan statusnya belum done
        mrs = self.sudo().search([('mr_status',  '!=', 'done'), ('originator_id', '!=', self.env.user.id)])
        # cari approval transaction/task yang waiting for approval
        approver = self.env['approval.task'].search(
            [('transaction_model_name', '=', self._name),
             ('transaction_id', 'in', mrs.ids),
             ('user_have_access_to_approval', '=', True),])
        ids = list(set(approver.mapped('transaction_id'))|set(originator_ids))
        _logger.info("TODO MRS IDS: %s", ids)
        return [('id', 'in', ids)]

    # Copy dari cni.purchase
    def button_request_approval(self):
        rec = self.ensure_one()
        rec.action_request_approval()

    def validate_request_approval(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Dokumen ini tidak bisa disetujui karena Material belum diisi."))
        for line in self.line_ids:
            if line.product_id.detailed_type == 'service':
                if line.product_id.pr_product_type_id.description != 'SERVICE':
                    raise UserError('''Product Type must be set to "SERVICE"''')
            else:
                if line.product_id.pr_product_type_id.description == 'SERVICE':
                    raise UserError('''You can't choose "SERVICE" as Product Type if PO Type is "Goods"''')

            if not line.priority:
                raise ValidationError(_("Priority tidak boleh kosong !"))
            if line.priority == 'P1' and not line.reason:
                raise ValidationError('Priority (P1), Reason tidak boleh kosong !')
        if self.odoo_id != 0:
            raise ValidationError('Approval from intra system')

    def get_priority_filter_matrix(self,approval_matrix_list):
        def check_cost_center_status(data):
            if data.approval_id.filter_by_cost_center and not data.skip_cost_center_check:
                # print("="*50+"Approval Analytic"+"="*50)
                # print(object.analytic_id.id)
                # print(data.group_id.mapped('users').mapped('account_analytic_ids').ids)
                users = data.get_users()
                return self.analytic_id and self.analytic_id.id in users.mapped('account_analytic_ids').ids
            else:
                return True
        return approval_matrix_list.filtered(lambda x :x.approval_type == '2' and check_cost_center_status(x))

    def event_approval_start(self):
        self.write({'mr_status': 'waiting', 'flag_reject': False})


    def button_approve_approval(self):
        rec = self.ensure_one()
        rec.action_approve()

    def event_before_approve(self,approval_transaction=None):
        group_cost_control = self.env.ref('metalindo_approval.group_finance_cost_control')
        if group_cost_control.id in approval_transaction.get_groups() :
            self.validate_approve_cost_control()

    def event_approval_done(self,is_approved=False):
        # if approval_sts == 0:
        if is_approved:
            self.write({
                'approved_by': self.approved_by or self.env.uid,
                'approved_date': self.approved_date or fields.Date.context_today(self),
                'done_by': None,
                'done_date': None,
                'mr_status': 'approved'
            })
            self.env['input.hs_code'].create({}).with_context(active_ids=[self.id]).action_done()
            self.check_state_done()


    def button_approve_cost_control(self):
        self.validate_approve_cost_control()

    def validate_approve_cost_control(self):
        for line in self.line_ids:
            if not line.account_id:
                raise UserError('Cost Element tidak boleh kosong, Silahkan update Cost Element')
