# -*- coding: utf-8 -*-
{
    'name': "Mail Template Internal",

    'summary': """Mail Template internal""",

    'description': """
Integrasi dengan Queue Job
Job Kita bisa generate email, simpan ke queue bawaan Odoo, lalu biarkan cron kirim.
Ini double buffering:
- queue_job → untuk jadwal proses generate email.
- mail queue → untuk jadwal proses kirim email.
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'send_message_email', 'send_message_whatsapp'],

    # always loaded
    'data': [
        'views/res_config_settings_views.xml',
    ],
}
