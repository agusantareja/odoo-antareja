# -*- coding: utf-8 -*-

from . import models
# from odoo import api, SUPERUSER_ID
#
#
# def post_init_hook(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     env['cni.approval.transaction'].migrate_to_approval_task('material.inventory.request', 'request_status', ['intercompany_approval', 'waiting'])
