from odoo.upgrade import util
from odoo import api, SUPERUSER_ID, _

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['cni.approval.transaction'].migrate_to_approval_task('material.inventory.request', 'request_status', ['intercompany_approval', 'waiting'])
