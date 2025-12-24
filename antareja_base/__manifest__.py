# -*- coding: utf-8 -*-

{
    'name': "Antareja Base",
    'summary': """Antareja Base""",
    'description': """
        This module adds a feature for Delegation of Authority (DOA).
        It allows users to delegate authority form access.
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Security & Access Rights',
    'version': '13.0.0.0.2',
    # any module necessary for this one to work correctly
    'depends': ['base','base_setup', 'mail'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/api_call_retry_views.xml',
        'views/application_server_views.xml',
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
