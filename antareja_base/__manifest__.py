# -*- coding: utf-8 -*-

{
    'name': "Antareja Base",
    'summary': """Antareja Base""",
    'description': """
        ANTAREJA
        
        Application 
        Notification
        Task Approval
        Authentication
        Resilience for API Call
        Jwt
        Authority
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://agus.ramdan.tech",
    'category': 'Base',
    'version': '13.0.0.0.6',
    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup', 'mail'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/application_server_views.xml',
        'views/application_server_auth_views.xml',
        'views/application_server_path_views.xml',
        'views/approval_audit_log_views.xml',
        'views/approval_task_views.xml',
        'views/approval_template_views.xml',
        'views/approval_instance_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/popup_reject.xml',
    ],
    'demo': [],
    'installable': True,
}
