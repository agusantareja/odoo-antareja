# -*- coding: utf-8 -*-

{
    'name': 'Antareja || Notification Ceria Mobile Intra',
    'version': '13.0.1.0.1',
    "category": "Extra Tools",
    "license" : "LGPL-3",
    'author': "Agus Muhammad Ramdan, Antareja Sinergi Sejahtera",
    'description': """ Ceria mobile yang ada di intra karena 
    """,
    'depends': ['base', 'mail','antareja_notification','antareja_integration'],
    'data': [
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/mobile_notification_views.xml',
        'views/menuitem.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}
