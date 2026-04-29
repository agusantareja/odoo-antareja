from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class recommend_qty_setting(models.Model):
    _name = 'recommend.qty.setting'
    _rec_name = 'code'


    code = fields.Text('Code')
    name = fields.Text('Variable')


    @api.constrains('code')
    def check_code(self):
        qty = self.env['stock.warehouse.orderpoint'].get_recommend_qty(10,100,10, 10, 10)
        if qty:
            return True