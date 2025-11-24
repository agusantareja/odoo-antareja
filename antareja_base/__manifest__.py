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
    'version': '13.0.0.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/approval_audit_log_views.xml',
        'views/approval_task_views.xml',
        'views/approval_template_views.xml',
        'views/approval_instance_views.xml',
    ],
    'demo': [],
    'installable': True,
}
