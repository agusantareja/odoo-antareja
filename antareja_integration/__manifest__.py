# -*- coding: utf-8 -*-

{
    'name': "Antareja || Integration",
    'summary': "Integration",

    'description': "Integration",

    'author': "IT Antareja",
    'website': "http://www.yourcompany.com",

    'category': 'Tools',
    'version': '13.0.3.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'amr_jsonrpc',
        'antareja_base',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/application_server_views.xml',
        'views/application_server_auth_views.xml',
        'views/application_server_path_views.xml',
        'views/menuitem.xml',
        'views/res_config_settings_views.xml',
    ],
}
