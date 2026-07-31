# -*- coding: utf-8 -*-
{
    'name': 'User Publik Key',
    'category': 'Tools',
    'description': "simulasi login dan approval process menggunakan qr. ",
    'author': 'Agus Muhammad Ramdan',
    'version': '13.0.0.0.0',
    'depends': ['base', 'web', 'amr_resource' ],
    'data': [
        'security/ir.model.access.csv',

        'views/user_public_key_views.xml',
        'views/menuitem.xml',
    ],
    'license': 'LGPL-3',
}
