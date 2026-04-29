# -*- coding: utf-8 -*-


from . import models

from odoo import api, SUPERUSER_ID, _

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = 'land.acquisition'
    records = env[model].search([('state', 'in', ['waiting','survey','cost_control'])])
    for rec in records:
        try:
            rec.register_approval_task()
        except BaseException as e:
            _logger = env['ir.logging']
            _logger.sudo().create({
                'name': 'post_init_hook_cni_approval_transaction',
                'type': 'server',
                'dbname': env.cr.dbname,
                'level': 'error',
                'message': _('Error registering approval task for transaction_id %s : %s') % (rec.id, str(e)),
                'path': 'post_init_hook',
                'func': 'post_init_hook',
                'line': '0',
            })
    records = env['land.acquisition.approval'].search(
        [('approval_audit_log_id', '=', False), ('la_id', '>', 0), ('status', '=', 'approved')]
    )
    for rec in records.with_context(__create_approval_audit_log_task=True, __create_rejected_audit_log_task=True):
        try:
            rec.create_audit_log(create_date=rec.create_date)
        except Exception as e:
            _logger = env['ir.logging']
            _logger.sudo().create({
                'name': 'post_init_hook_cni_approval_transaction',
                'type': 'server',
                'dbname': env.cr.dbname,
                'level': 'error',
                'message': _('Error registering approval task for transaction_id %s: %s') % (str(rec), str(e)),
                'path': 'post_init_hook',
                'func': 'post_init_hook',
                'line': '0',
            })

    records = env['land.acquisition.survey.approval'].search(
        [('approval_audit_log_id', '=', False), ('la_id', '>', 0), ('status', '=', 'approved')]
    )
    for rec in records.with_context(__create_approval_audit_log_task=True, __create_rejected_audit_log_task=True):
        try:
            rec.create_audit_log(create_date=rec.create_date)
        except Exception as e:
            _logger = env['ir.logging']
            _logger.sudo().create({
                'name': 'post_init_hook_cni_approval_transaction',
                'type': 'server',
                'dbname': env.cr.dbname,
                'level': 'error',
                'message': _('Error registering approval task for transaction_id %s: %s') % (str(rec), str(e)),
                'path': 'post_init_hook',
                'func': 'post_init_hook',
                'line': '0',
            })

    # update mobile approval
    env['approval.task'].search([('transaction_model_name', '=', model),('transaction_id', '>', 0)]).send_to_mobile_approval()
