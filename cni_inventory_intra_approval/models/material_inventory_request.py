from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MaterialInventoryRequest(models.Model):
    _name = 'material.inventory.request'
    _inherit = [_name, 'approval.transaction.mixin', 'mail.template.internal.mixin']

    # stage_inline_mir_id = fields.Many2one(
    #     'approval.transaction.stage'
    # )

    def get_internal_menu_id(self):
        return self.env.ref('cni_inventory_intra.root_menu_material_request').id

    def get_requester_id(self):
        return self.ensure_one().request_by.id

    def get_approval_template_id(self):
        return self.env.ref('cni_inventory_intra.mir_approver_mail_template').id

    def set_transaction_status(self, state):
        """
        Set the status of the material requisition.
        """
        self.ensure_one().write({'request_status': state})

    def get_transaction_status(self):
        """
        Returns the current status of the material requisition.
        """
        return self.ensure_one().request_status
    def set_starting_status_approval(self):
        """
        Starting status approval
        """
        self.set_transaction_status('intercompany_approval')

    def action_submit_request(self):
        for rec in self:
            rec.reset_line_approval()
            rec.validate_before_change_state('draft', 'intercompany_approval')
            #rec.write({'request_status': 'intercompany_approval'})
            rec.strategy_button_submit()

    def reset_line_approval(self):
        """
        Bila pernah di reject perlu di reset
        """
        self.ensure_one()
        if not self.approval_ids or self.approval_ids.filtered(lambda f: f.status_approval == 'rejected'):
            self.approval_ids.reset_task_approval()

    def validate_before_change_state(self,from_state, to_state):
        self.ensure_one()
        if not self.line_ids:
            raise UserError("Product Harus Diisi")
        for line in self.line_ids:
            if line.qty_issue <= 0:
                raise UserError("Quantity Harus lebih besar dari 0")

    def callback_approval_stage_rejected(self, approval_stage):
        super().callback_approval_stage_rejected(approval_stage)
        message = "Note Reject => %s" % (self.env.context.get('__reject_reason'))
        # mail bot
        self.write({
                # 'approval_ids': False,
                'flag_note': True,
                'notes': message + " by " + str(self.env.user.partner_id.name)
        })


    def get_acces_button(self):
        for rec in self:
            rec.acces_button = self.access_approval

    def _get_approval_requests(self):
        return {
            'domain': [('access_approval', '=', True), ('request_status', '=', 'intercompany_approval')],
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

    def search_filter_mir(self, operator, operand):
        if self._uid in [1, 2]:
            return []
        if self.user_has_groups('base.group_erp_manager'):
            return []
        else:
            user = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
            department_id = False
            if user.sudo().department_id.category_id.tingkatan > 2:
                department_id = user.sudo().department_id.parent_id
            elif user.sudo().department_id.category_id.tingkatan == 2:
                department_id = user.sudo().department_id
            elif user.sudo().department_id.category_id.tingkatan < 2:
                department_id = user.sudo().department_id
            ids = self.search([('request_by', '=', self._uid)]).ids
            ids2 = self.env['material.inventory.request'].search([('access_approval', '=', True)]).ids
            ids3 = self.env['material.inventory.request'].search([('department_id', '=', department_id.id)]).ids
            return [('id', 'in', list(set(ids+ids2+ids3)))]
