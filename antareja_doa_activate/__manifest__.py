# -*- coding: utf-8 -*-
{
    'name': "Delegation of Authority (DoA) Activate",
    'summary': """
        Delegation of Authority (DoA)
        """,
    'description': """
        This module activate a feature for Delegation of Authority (DOA).
        It allows users to delegate authority form access.
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Security & Access Rights',
    'version': '13.0.0.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'antareja_base', 'antareja_doa'],
    # always loaded
    'data': [
        'views/approval_audit_log_views.xml',
        'views/approval_task_views.xml',
    ],
}
