# -*- coding: utf-8 -*-

from . import models

from odoo import api, SUPERUSER_ID, _

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = 'material.inventory.request'

    records = env['approval.task'].search([('transaction_model_name','=',model)])

    for rec in records:
        approval_instance = env['cni.approval.instance'].create_or_get(
            transaction_model_name=rec.transaction_model_name,
            transaction_id=rec.transaction_id,
            view_name=rec.view_name
        )
        if approval_instance.is_status_waiting_approval():
            approval_instance.register_approval_transaction_task()
        else:
            approval_instance.unregister_approval_transaction_task()
    approval_transaction = env['cni.approval.transaction']
    data_records = approval_transaction.read_group(
        domain=[('transaction_id', '>', 0),('form_id.model', '=', model),('sts','=','1')],
        fields=['transaction_id', 'form_id', 'id:min'],
        groupby=['transaction_id', 'form_id']
    )
    for group in data_records:
        group_domain = group['__domain']
        records_in_group = approval_transaction.search(group_domain,limit=1, order='seq asc, id asc')
        try:
            if records_in_group:
                approval_instance = env['cni.approval.instance'].create_or_get(
                    transaction_model_name=records_in_group.transaction_model_name,
                    transaction_id=records_in_group.transaction_id,
                    view_name=records_in_group.view_name
                )
                if approval_instance.is_status_waiting_approval():
                    approval_instance.register_approval_transaction_task()
                else:
                    approval_instance.unregister_approval_transaction_task()

        except Exception  as e:
            _logger = env['ir.logging']
            _logger.sudo().create({
                'name': 'post_init_hook_cni_approval_transaction',
                'type': 'server',
                'dbname': env.cr.dbname,
                'level': 'error',
                'message': _('Error registering approval task for transaction_id %s: %s') % (str(group), str(e)),
                'path': 'post_init_hook',
                'func': 'post_init_hook',
                'line': '0',
            })

    records = env['cni.approval.transaction'].search(
        [('form_id.model', '=', model),('approval_audit_log_id', '=', False),('transaction_id', '>', 0),('sts','in',['2','3'])]
    )

    for rec in records.with_context(__create_approval_audit_log_task=True,__create_rejected_audit_log_task=True):
        try:
            rec.create_audit_log()
        except Exception  as e:
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
