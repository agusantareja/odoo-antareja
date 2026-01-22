# -*- coding: utf-8 -*-

{
    'name': 'AMR JSON-RPC Demo',
    'version': '1.0.0',
    'summary': 'Demo addon untuk JSON-RPC dan model sederhana',
    'description': """
AMR JSON-RPC Demo
=================
Addon contoh:
- Model sederhana
- View tree & form
- Cocok untuk demo integrasi JSON-RPC
""",
    'author': "Agus Muhammad Ramdan",
    'license': "AGPL-3",
    'website': "http://agus.ramdan.tech",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/external_event_line_views.xml',
    ],
    'installable': True,
    'application': False,
}
