# -*- coding: utf-8 -*-

{
    'name': "Antareja || Integration Sync",

    'summary': "Integration Sync",

    'description': "Integration Sync",

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.agus.ramdan.tech",

    'category': 'Tools',
    'version': '13.0.2.2.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'antareja_base',
        'antareja_integration',
        'amr_data_sync',
    ],
    # always loaded
    'data': [
        'views/server_sync_views.xml',
    ],
}
