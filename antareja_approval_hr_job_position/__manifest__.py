# -*- coding: utf-8 -*-
{
    'name': "Base",
    'summary': """Antareja base, HR Job Position""",
    'description': """
        This module adds a feature for Delegation of Authority (DOA).
        It allows users to delegate authority form access.
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Security & Access Rights',
    'version': '13.0.0.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base','antareja_base','hr'],
    # always loaded
    'data': [
        'views/approval_audit_log_views.xml',
    ],
    'demo': [],
    'installable': True,
}
