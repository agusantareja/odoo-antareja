# -*- coding: utf-8 -*-
{
    'name': "Antarja || Integration",

    'summary': """Integartion Integartion""",

    'description': """
        Integartion 
    """,

    'author': "IT Antareja",
    'website': "http://www.yourcompany.com",

    'category': 'Tools',
    'version': '13.0.2.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'amr_jsonrpc',
        'antareja_base'
    ],
    # always loaded
    'data': [
        'data/cron.xml',
        'views/application_server_auth_views.xml',
        'views/menuitem.xml',
        'views/res_config_settings_views.xml',
    ],

}
