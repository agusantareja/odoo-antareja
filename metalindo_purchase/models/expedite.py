from odoo import models, fields, tools, _

class Expedite(models.Model):
    _name = 'expedite'
    _description = 'Expedite'
    _auto = False
    _rec_name = 'po_line_name'

    pr_id = fields.Many2one('material.requisition', string='PR No.')
    po_id = fields.Many2one('purchase.order', string='PO No.')
    po_type = fields.Selection([('service','Service'),('consu','Goods')], string='PO Type') #
    po_partner_id = fields.Many2one('res.partner', string='Vendor Name')
    po_person_partner_id = fields.Many2one('res.partner', string='Contact Person')
    po_person_email = fields.Char(string='Email')
    po_person_number = fields.Char(string='Phone')
    po_line_item_number = fields.Integer(string='PO Item Number')
    po_line_product_id = fields.Many2one('product.product', string='Material Short Description')
    po_line_name = fields.Char(string='Material Long Description')
    po_create_date = fields.Datetime(string='PO Create Date')
    po_line_date_planned = fields.Datetime(string='PO Due Date')
    pr_requestor = fields.Char(string='PR Requestor')
    pr_delivery_location_id = fields.Many2one('res.partner', string='Drop Point')
    po_picking_type_id = fields.Many2one('stock.picking.type', string='Delivery Method')


    def view_po(self):
        action = {
            'name':_('Purchase Order'),
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'self',
            'res_id' : self.po_id.id,
        }
        return action

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW expedite AS (
                SELECT
                    pol.id AS id,
                    mr.id AS pr_id,
                    pol.order_id AS po_id,
                    po.po_type AS po_type,
                    po.partner_id AS po_partner_id,
                    rp.id AS po_person_partner_id,
                    rp.email AS po_person_email,
                    rp.phone AS po_person_number,
                    pol.item_no AS po_line_item_number,
                    pol.product_id AS po_line_product_id,
                    pol.name AS po_line_name,
                    po.create_date AS po_create_date,
                    pol.date_planned AS po_line_date_planned,
                    mr.request_by AS pr_requestor,
                    mr.delivery_location_id AS pr_delivery_location_id,
                    po.picking_type_id AS po_picking_type_id

                FROM purchase_order_line pol
                LEFT JOIN purchase_order po ON pol.order_id = po.id
                LEFT JOIN LATERAL (
                    SELECT
                        COALESCE(child.id, vendor.id) AS id,
                        COALESCE(child.email, vendor.email) AS email,
                        COALESCE(child.phone, vendor.phone) AS phone
                    FROM res_partner vendor
                    LEFT JOIN LATERAL (
                        SELECT c.id, c.email, c.phone
                        FROM res_partner c
                        WHERE c.parent_id = vendor.id
                        ORDER BY c.id
                        LIMIT 1
                    ) child ON TRUE
                    WHERE vendor.id = po.partner_id
                ) rp ON TRUE
                LEFT JOIN material_requisition_line mrl ON pol.mr_line_id = mrl.id
                LEFT JOIN material_requisition mr ON mrl.mr_id = mr.id
                WHERE po.state IN ('purchase', 'done') 
                AND pol.qty_received < pol.product_qty
                AND (
                    pol.mr_line_id IS NULL
                    OR (pol.mr_line_id IS NOT NULL AND mr.active IS TRUE)
                )
            )
        """)
