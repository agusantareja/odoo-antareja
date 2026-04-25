from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MaterialInventoryRequest(models.Model):
    _name = 'leave.leave_request'
    _inherit = [_name, 'approval.transaction.mixin', 'mail.template.internal.mixin']

    stage_inline_lr_id = fields.Many2one(
        'approval.transaction.stage'
    )
    def get_requester_id(self):
        return self.ensure_one().employee_id.user_id.id
    # def get_internal_menu_id(self):
    #     return self.env.ref('cni_inventory_intra.root_menu_material_request').id
    #
    # def get_approval_template_id(self):
    #     return self.env.ref('cni_inventory_intra.mir_approver_mail_template').id

    # def set_transaction_status(self, state):
    #     """
    #     Set the status of the material requisition.
    #     """
    #     self.ensure_one().write({'status': state})
    #
    # def get_transaction_status(self):
    #     """
    #     Returns the current status of the material requisition.
    #     """
    #     return self.ensure_one().status
    def set_starting_status_approval(self):
        """
        Starting status approval
        """
        self.set_transaction_status('submitted')

    def button_submit(self):
        for rec in self:
            rec.reset_line_approval()
            rec.validate_before_change_state('draft', 'submitted')
            approvals = self.env['leave.leave_approval'].search(
                [('lr_id', '=', rec.id), ('status', '=', 'waiting_approval')], limit=1, order='id asc')

            if len(rec.leave_approval_ids) == 1:
                rec.write({
                    'kondisi':'1',
                    'list_approver':approvals.employee_id.name
                    })
            elif len(rec.leave_approval_ids) > 1:
                app1_waiting = self.env['leave.leave_approval'].sudo().search([('lr_id','=',rec.id)],order='id asc', limit=1)
                if app1_waiting.status == 'waiting_approval':
                    rec.write({
                        'kondisi':'2',
                        'list_approver':app1_waiting.employee_id.name})

            if rec.odoo_id:
                if rec.is_leave_revisi or rec.is_leave_cancel:
                    rec.update_lr_from_revisi()
            else:
                rec.create_leave_request()

            rec.strategy_button_submit()

    def validate_before_change_state(self,from_state, to_state):
        rec = self.ensure_one()
        if not rec.leave_days:
            raise ValidationError(_("Days Harus Diisi"))

        if rec.balance == 0:
            pass
        elif len(rec.leave_days) > rec.balance:
            if rec.state != 'validated':
                raise ValidationError(_("Hari yang dipilih tidak boleh melebihi dari %s" % str(rec.balance)))

        if not rec.leave_type.is_field_break:
            for day in rec.leave_days:
                if day.leave_balance_total < 0 and day.leave_balance_id:
                    raise ValidationError(_("Tidak ditemukan Saldo Cuti"))

        if rec.leave_type.is_compensatory:
            for day in rec.leave_days:
                if day.leave_balance_id == False:
                    raise ValidationError(_("Tidak ditemukan Saldo Cuti Compensatory"))

        if rec.leave_days:
            list_days = []
            for line in rec.leave_days:
                if line.date in list_days:
                    raise ValidationError(_("Tanggal duplicate"))
                list_days.append(line.date)
                if line.leave_balance_id.balance_full_used:
                    if (line.leave_balance_id.balance - line.leave_balance_id.balance_reserved) < 0:
                        raise ValidationError(_("Maaf, Saldo Anda Sudah Habis"))

        attachments = self.env['ir.attachment'].sudo().search([('res_model', '=', self._name), ('res_id', '=', rec.id)])
        if rec.leave_type.attachment == True:
            if not attachments:
                raise ValidationError(_("Attachment Harus Diisi"))

    def callback_approval_stage_rejected(self, approval_stage):
        super().callback_approval_stage_rejected(approval_stage)
        message = "Note Reject => %s" % (self.env.context.get('__reject_reason'))
        # mail bot
        self.write({
                'flag_note': True,
                'notes': message + " by " + str(self.env.user.partner_id.name)
        })

    def reset_line_approval(self):
        """
        Bila pernah di reject perlu di reset
        """
        self.ensure_one()
        if not self.leave_approval_ids or self.leave_approval_ids.filtered(lambda f: f.status_approval == 'rejected'):
            self.write({ 'leave_approval_ids': False,})
            self.append_approval()


    def get_access_button(self):
        for rec in self:
            rec.access_button = self.access_approval

    def _get_approval_requests(self):
        return {
            'domain': [('access_approval', '=', True), ('state', '=', 'submitted')],
            #'domain': [('id', 'in', data)],
            'view_mode': 'tree,form,kanban',
            'res_model': self._name,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('To Approve'),
            # 'res_id': self.id,
            'target': 'current',
            'context': {
                'create': 0,
                'delete': 0
            }
        }

    def search_filter_waiting(self, operator, operand):
        """untuk menu approval"""
        # data = []
        #
        # for lr in self.env['leave.leave_request'].sudo().search([('state', '=', 'submitted')]):
        #     # LIST TAB APPROVAL
        #     for approval in lr.leave_approval_ids:
        #         if approval.employee_id.id == self.env.uid and approval.status == 'waiting_approval':
        #             data.append(lr.id)

        return [('state', '=', 'submitted'),('access_approval', '=', True)]
