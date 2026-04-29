from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)



class create_purchase_wizard(models.TransientModel):
    _name = 'create.purchase.wizard'


    procurement_type = fields.Selection([
        ('Purchase Order','Purchase Order'),
        ('Call for Tender','Call for Tender'),
    ])

    def create_purchase(self, action, recommend_qty_ids, context):
        view_id = self.env.ref('purchase.purchase_order_form').id
        action.update({
            'views': [[view_id, 'form']],
            'name': _('Direct Purchase'),
            'res_model': 'purchase.order',
        })

        analytic_default = self.env.ref('metalindo_purchase.warehouse_analytic_account', raise_if_not_found=False)
        if not analytic_default:
            raise UserError('Mohon dibuatkan Cost Center dengan name="warehouse"')

        default_analytic_id = self.env['metalindo.analytic'].search([('name', '=', 'warehouse')], limit=1)
        if not default_analytic_id:
            raise UserError('Mohon dibuatkan metalindo.analytic dengan name="warehouse"')

        merged_lines = {}

        for rec in recommend_qty_ids:
            key = rec.product_id.id
            if key not in merged_lines:
                merged_lines[key] = {
                    'product_id': rec.product_id.id,
                    'name': rec.product_id.product_desc,
                    'product_uom': rec.product_id.uom_id.id,
                    'product_qty': rec.outstanding_qty,
                    'price_unit': 0.0,
                    'price_view': 0.0,
                    'date_planned': datetime.now(),
                    'analytic_id': rec.product_id.categ_id.analytic_id.id or default_analytic_id.id,
                    'recommend_qty_ids': [rec.id],
                    'purchase_category_id': rec.product_id.product_tmpl_id.purchase_category_id.id,
                    'hs_code': rec.product_id.product_tmpl_id.hs_code,
                }
            else:
                merged_lines[key]['product_qty'] += rec.outstanding_qty
                merged_lines[key]['recommend_qty_ids'].append(rec.id)

        order_line = [
            (0, 0, {
                **line,
                'recommend_qty_ids': [fields.Command.set(line.get('recommend_qty_ids', []))],
            })
            for line in merged_lines.values()
        ]

        context.update({
            'default_po_type': 'consu',
            'default_order_line': order_line,
            'default_recommended': True,
            'recommended_qty': True,
            'default_is_scm_buyer': True,
        })

    def create_requisition(self,action,recommend_qty_ids,context):
        view_id = self.env.ref('purchase_requisition.view_purchase_requisition_form').id
        action.update({
            'views': [[view_id, 'form']],
            'name' : _(self.procurement_type),
            'res_model' : 'purchase.requisition',
        })
        analytic_id = self.env.ref('metalindo_purchase.warehouse_analytic_account')
        # Get cost center
        if analytic_id:
            analytic_id = self.env['metalindo.analytic'].search([('name', '=', 'warehouse')], limit=1)
        else:
            raise UserError('Mohon dibuatkan Cost Center dengan name="warehouse"')

        merged_lines = {}
        origin = []
        for this in recommend_qty_ids:
            key = this.product_id.id
            origin.append(this.name)
            if key not in merged_lines:
                merged_lines[key] = {
                    'product_id' : this.product_id.id,
                    'product_desc' : this.product_desc,
                    'product_qty' : this.outstanding_qty,
                    'product_uom_id': this.product_id.uom_id.id,
                    'purchase_request_id': False,
                    'recommend_qty_ids': [this.id],
                    'analytic_id': this.product_id.categ_id.analytic_id.id or analytic_id,
                    'purchase_category_id': this.product_id.product_tmpl_id.purchase_category_id.id,
                    'hs_code': this.product_id.product_tmpl_id.hs_code,
                }
            else:
                merged_lines[key]['product_qty'] += this.outstanding_qty
                merged_lines[key]['recommend_qty_ids'].append(this.id)

        line_ids = [
            (0, 0, {
                **line,
                'recommend_qty_ids': [fields.Command.set(line.get('recommend_qty_ids', []))],
            })
            for line in merged_lines.values()
        ]

        requisition_type_id = self.env['purchase.requisition.type'].search([('name','=',self.procurement_type)],limit=1)
        context.update({
            'default_po_type': 'consu',
            'default_line_ids': line_ids,
            'default_origin': ', '.join(origin),
            'default_type_id' : requisition_type_id.id,
            'default_recommended' : True,
        })

    def action_create_purchase(self):
        recommend_qty_ids = []
        model_name = self.env.context.get('active_model')
        for res_id in self.env.context.get('active_ids'):
            recommend_qty_id = self.env[model_name].sudo().browse(int(res_id))
            recommend_qty_ids.append(recommend_qty_id)

        action = {}
        context = {'default_user_id': self.env.user.id}
        if self.procurement_type == 'Purchase Order':
            self.create_purchase(action,recommend_qty_ids,context)
        else:
            self.create_requisition(action,recommend_qty_ids,context)
        
        action.update({
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_mode': 'form',
            'context' : context,
        })
       
        return action
    

class blanket_order_confirm_wizard(models.TransientModel):
    _name = 'blanket.order.confirm.wizard'

    info = fields.Text()

    def create_purchase(self):
        context = self.env.context.get('next_context')
        action = self.env.context.get('next_action')
        action.update({
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_mode': 'form',
            'context' : context,
        })
        return action