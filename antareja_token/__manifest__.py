# -*- coding: utf-8 -*-

{
    'name': "JWT",
    'summary': """
        JWT,
        Sharing Trusted Token Authentication between Applications Server
    """,
    'description': """
        Sharing Trusted Token Authentication between Applications Server
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'API',
    'version': '16.0.0.0.8',
    'depends': ['base', 'antareja_base', ],
    'external_dependencies': {
        'python': ['pyjwt'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/antareja_token_audience_views.xml',
        'views/antareja_token_issuer_views.xml',
        'views/res_config_settings_views.xml',
    ],
}
