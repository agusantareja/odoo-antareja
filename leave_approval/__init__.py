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
                    WHERE table_name='leave_leave_approval'
                    AND column_name='date_execution'
                ) THEN
                    ALTER TABLE leave_leave_approval
                    ADD COLUMN date_execution TIMESTAMP;
                END IF;
            END;
            $$;
        """)
    cr.execute("""
                update leave_leave_approval set date_execution=write_date  where status='approved' and date_execution is null;
            """)


def post_init_hook_function(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # untuk yang sudah d
    cr.execute("""
    
    update leave_leave_approval set status_approval = 'approved' where status= 'approved' and status_approval is null ;
    update leave_leave_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval is null  ;
    update leave_leave_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval = 'draft';
    
    update leave_compensatory_request_approval set status_approval = 'approved' where status= 'approved' and status_approval is null ;
    update leave_compensatory_request_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval is null  ;
    update leave_compensatory_request_approval set status_approval = 'waiting_approval' where status= 'waiting_approval' and status_approval = 'draft';
    
   
   
    """)

    records = env['leave.leave_request'].search([('state', '=', 'submitted')])
    for rec in records:
        try:
            rec.with_context(__ignore_notify_approval_by_user=True).strategy_button_submit()
            rec.flush()
        except Exception as ase:
            env['ir.logging'].create({
                'name': 'leave_approval',
                'type': 'server',
                'level': 'error',
                'message': f'Error creating approval for {rec.name}: {str(ase)}',
                'path': 'leave_approval/__init__.py',
                'func': 'post_init_hook_function',
                'line': 1,
            })

    records = env['leave.compensatory_request'].search([('state', '=', 'submitted')])
    for rec in records:
        try:
            rec.with_context(__ignore_notify_approval_by_user=True).strategy_button_submit()
            rec.flush()
        except Exception as ase:
            env['ir.logging'].create({
                'name': 'compensatory_request',
                'type': 'server',
                'level': 'error',
                'message': f'Error creating approval for {rec.name}: {str(ase)}',
                'path': 'leave_approval/__init__.py',
                'func': 'post_init_hook_function',
                'line': 1,
            })
