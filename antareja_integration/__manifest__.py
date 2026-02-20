# -*- coding: utf-8 -*-

{
    'name': "Antarja || Integration",
    'summary': """Integration""",

    'description': """
        Integration 
    """,

    'author': "IT Antareja",
    'website': "http://www.yourcompany.com",

    'category': 'Tools',
    'version': '13.0.3.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'amr_jsonrpc',
        'antareja_base'
    ],
    # always loaded
    'data': [
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/application_server_views.xml',
        'views/application_server_auth_views.xml',
        'views/application_server_path_views.xml',
        'views/menuitem.xml',
    ],

}
