from . import models

from odoo import api, SUPERUSER_ID

def pre_init_hook_function(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # create col date execution
    cr.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='material_requisition_approval'
                    AND column_name='date_execution'
                ) THEN
                    ALTER TABLE material_requisition_approval
                    ADD COLUMN date_execution TIMESTAMP;
                END IF;
            END;
            $$;
        """)
    cr.execute("""
                update material_requisition_approval set date_execution=write_date  where approve=true and date_execution is null;
            """)
    # copy data update material_requisition_approval set date_execution=write_date ke  where approve=true
    cr.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='material_inventory_request_approval'
                        AND column_name='date_execution'
                    ) THEN
                        ALTER TABLE material_inventory_request_approval
                        ADD COLUMN date_execution TIMESTAMP;
                    END IF;
                END;
                $$;
            """)
    cr.execute("""
                    update material_inventory_request_approval set date_execution=write_date where approve=true and date_execution is null;
                """)

def post_init_hook_function(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # untuk yang sudah d
    cr.execute("""
    
    update material_requisition_approval set status_approval = 'approved' where status= 'approved' and status_approval is null and approve = true;
    update material_requisition_approval set status_approval = 'approved' where status= 'approved' and status_approval is null ;
    update material_requisition_approval set status_approval = 'approved' where status= 'approved' and status_approval = '2';
    update material_requisition_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval is null  ;
    update material_requisition_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval = '1';
    update material_requisition_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval = 'draft';
    
    update material_inventory_request_approval set status_approval = 'approved' where status= 'approved' and status_approval is null and approve = true;
    update material_inventory_request_approval set status_approval = 'approved' where status= 'approved' and status_approval is null ;
    update material_inventory_request_approval set status_approval = 'approved' where status= 'approved' and status_approval = '2';
    update material_inventory_request_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval is null  ;
    update material_inventory_request_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval = '1';
    update material_inventory_request_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval = 'draft';
    """)

    # create_audit_trial(self, action_type, proxy_user_id=None, ignore_message
    records = env['material.inventory.request'].search([('request_status', '=', 'intercompany_approval')])
    for rec in records:
        try:
            approval_instance = rec.ensure_approval_instance()
            approval_instance.write({'stage_status': rec.state})
            approval_instance.with_context(__ignore_notify_approval_by_users=True).setup_approval_stage()
            approval_instance.flush()
        except Exception as ase:
            env['ir.logging'].create({
                'name': 'cni_inventory_intra_approval',
                'type': 'server',
                'level': 'error',
                'message': f'Error creating approval for {rec.name}: {str(ase)}',
                'path': 'cni_inventory_intra_approval/__init__.py',
                'func': 'post_init_hook_function',
                'line': 1,
            })

    records = env['material.requisition'].search([('request_status', 'in',['cost_control','waiting_approval',])])
    for rec in records:
        try:
            approval_instance = rec.ensure_approval_instance()
            approval_instance.write({'stage_status': rec.state})
            approval_instance.with_context(__ignore_notify_approval_by_users=True).setup_approval_stage()
            approval_instance.flush()
        except Exception as ase:
            env['ir.logging'].create({
                'name': 'cni_inventory_intra_approval',
                'type': 'server',
                'level': 'error',
                'message': f'Error creating stage_cost_control_id for {rec.name}: {str(ase)}',
                'path': 'cni_inventory_intra_approval/__init__.py',
                'func': 'post_init_hook_function',
                'line': 1,
            })
