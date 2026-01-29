# -*- coding: utf-8 -*-
{
    'name': "Antarja || Integartion Sync",

    'summary': """Integartion Sync""",

    'description': """
        Integartion Sync
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.agus.ramdan.tech",

    'category': 'Tools',
    'version': '13.0.2.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'antareja_base',
        'amr_data_sync',
        'amr_data_sync_event'
    ],
    # always loaded
    'data': [
        'views/server_sync_views.xml',
    ],

}
