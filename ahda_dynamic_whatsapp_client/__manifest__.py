# -*- coding: utf-8 -*-

{
    'name': 'AHDA Dynamic WhatsApp API Client',
    'version': '16.0.1.0.1',
    'summary': 'A fully configurable WhatsApp API client for Odoo, supporting template-based messaging, partner targeting, and automation.',
    'author': 'AHDA Tech Solution',
    'category': 'Tools',
    'depends': ['base', 'base_automation'],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/whatsapp_api.xml',

        # Views
        'views/ir_actions_server_views.xml',
        'views/whatsapp_template_views.xml',
        'views/whatsapp_api.xml',
        'views/whatsapp_log_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'price': 49,
    'currency': 'EUR',
    'license': 'LGPL-3',
}
