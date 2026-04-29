# -*- coding: utf-8 -*-

from . import models

from odoo import api, SUPERUSER_ID, _

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = 'rencana.tindak.lanjut'
    records = env[model].search([('state', 'in',['open','progress','waiting'])])
    for rec in records:
        try:
            rec.register_approval_task()
        except BaseException  as e:
            _logger = env['ir.logging']
            _logger.sudo().create({
                'name': 'post_init_hook_leave_approval',
                'type': 'server',
                'dbname': env.cr.dbname,
                'level': 'error',
                'message': _('Error registering approval task for transaction_id %s : %s') % (rec.id,str(e)),
                'path': 'post_init_hook',
                'func': 'post_init_hook',
                'line': '0',
            })

    records = env['rencana.tindak.lanjut.approval'].search(
        [('approval_audit_log_id', '=', False),('state','in',['approved','rejected'])]
    )
    for rec in records.with_context(__create_approval_audit_log_task=True,__create_rejected_audit_log_task=True):
        try:
            rec.lr_id and rec.create_audit_log(create_date=rec.create_date)
        except Exception  as e:
            _logger = env['ir.logging']
            _logger.sudo().create({
                'name': 'post_init_hook_leave_approval',
                'type': 'server',
                'dbname': env.cr.dbname,
                'level': 'error',
                'message': _('Error registering approval task for transaction_id %s: %s') % (str(rec), str(e)),
                'path': 'post_init_hook',
                'func': 'post_init_hook',
                'line': '0',
            })

    env['approval.task'].search([('transaction_model_name', '=', model), ('transaction_id', '>', 0)]).send_to_mobile_approval()