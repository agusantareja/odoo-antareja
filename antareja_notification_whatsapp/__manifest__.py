# -*- coding: utf-8 -*-

{
    'name': "Notification WhatsApp Client",
    'summary': """Notification WhatsApp Client and Integration """,
    'description': """Notification WhatsApp Client and Integration""",
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.agus.ramdan.tech",
    'category': 'Uncategorized',
    'version': '16.0.1.0.0.2',
    'depends': ['base', 'mail', 'ahda_dynamic_whatsapp_client', 'antareja_notification'],
    # always loaded
    'data': [
        'data/cron.xml',
        'views/whatsapp_log_views.xml',
        'views/notification_template_views.xml',
        'views/notification_log_views.xml',
        'views/res_config_settings_views.xml',
    ],
}
