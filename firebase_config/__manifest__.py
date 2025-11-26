# -*- coding: utf-8 -*-
{
    'name': 'Firebase Configuration',
    'version': '13.0',
    'category': 'Settings',
    'summary': 'UI for storing Firebase service account JSON',
    'depends': ['base'],
    'external_dependencies': {
        'python': ['firebase_admin'],
    },
    'data': [
        'wizard/firebase_load_wizard.xml',
        'views/firebase_config_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,

}
