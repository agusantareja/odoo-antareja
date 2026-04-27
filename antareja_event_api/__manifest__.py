# -*- coding: utf-8 -*-

{
    'name': 'REST API For Event',
    'version': '13.0.0.0.1',
    'category': 'API',
    'author': 'Agus Muhammad Ramdan',
    'website': 'https://agus.ramdan.tech',
    'summary': 'REST API For Odoo',
    'description': """
this api modify from Odoo    
REST API For Odoo
====================
With use of this module user can enable REST API in any Odoo applications/modules

For detailed example of REST API refer *readme.md*
""",
    'depends': [
        'base', 'web', 'antareja_token', 'antareja_base', 'amr_data_event', 'antareja_sync_api'
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
}
