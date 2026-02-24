# -*- coding: utf-8 -*-
{
    'name': "DOA || Intra Integartion",
    'summary': """
        DOA Intra Integartion 
        """,
    'description': """
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.0.0.0',
    'depends': [
        'base', 'mail', 'amr_data_sync', 'antareja_doa', 'antareja_integration' ,
        'antareja_integration_app_intra_cerindocorp', 'antareja_integration_sync'
    ],
    # always loaded
    'data': [
        'data/external_server_sync_data.xml',
        'data/user_delegation_data.xml',
    ],
}
