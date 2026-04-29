from odoo.upgrade import util
from odoo import api, SUPERUSER_ID, _

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['cni.approval.transaction'].migrate_to_approval_task('purchase.order', 'state', ['waiting_for_approval'])
