# -*- coding: utf-8 -*-

{
    'name': 'Antareja || Notification',
    'version': '13.0.1.0.2',
    "category": "Extra Tools",
    "license" : "LGPL-3",
    'author': "Agus Muhammad Ramdan, Antareja Sinergi Sejahtera",
    'description': """Module untuk mengirim notifikasi via email/WhatsApp dengan menggunakan template yang sudah 
    disediakan untuk penyederhanaan pengiriman email/WhatsApp.
    """,
    'depends': ['base', 'mail', 'antareja_base',],
    'data': [
        'security/ir.model.access.csv',
        'views/approval_task_views.xml',
        'views/notification_template_views.xml',
        'views/notification_log_views.xml',
        'views/approval_template_views.xml',
        'views/notification_mobile_template_views.xml',
        'views/menuitem.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}
