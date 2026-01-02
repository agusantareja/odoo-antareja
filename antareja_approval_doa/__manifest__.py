# -*- coding: utf-8 -*-
{
    'name': "Approval || Doa",

    'summary': """
        Add Feature DOA to Approval Task
        
        Fokus to 
        - notification and audit log
        - access and search filter
        - approval process
        """,

    'description': """
    
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    'category': 'Approval & Delegation of Authority',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'antareja_approval','antareja_approval_notif', 'antareja_doa', 'antareja_doa_notif',],

    # always loaded
    'data': [
        'views/approval_transaction_task_views.xml',
        'views/approval_audit_log_views.xml',
    ],
}
