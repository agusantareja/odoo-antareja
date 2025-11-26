# -*- coding: utf-8 -*-
{
    'name': "Notification Whatapp Client",
    'summary': """Notification Whatapp Client and Integration """,
    'description': """Notification Whatapp Client and Integration""",
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.1.0.0.1',
    'depends': ['base', 'mail', 'ahda_dynamic_whatsapp_client'],
    # always loaded
    'data': [
        'data/cron.xml',
        'views/whatsapp_log_views.xml',
    ],
}
