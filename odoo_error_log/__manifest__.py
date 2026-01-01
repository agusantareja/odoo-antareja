# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "odoo error log",

    'summary': """
      Odoo Error Log
        """,
    'description': "",

    'category': 'Extra Tools',
    'version': '14.0.0.1',
    "author":  "Mo Li",
    'depends': ['web'],
    'data': [
        'data/ir_config_parameter_data.xml',
        'security/ir.model.access.csv',
        'views/error_log_views.xml',
        'views/templates.xml'
    ],
    "images":  ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    "license": "AGPL-3",
}
