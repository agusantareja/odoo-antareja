# -*- coding: utf-8 -*-
{
    'name': "Antarja || Approval Manager",

    'summary': """Integartion Approval Manager""",

    'description': """
        Integartion Approval Manager
    """,

    'author': "IT Antareja",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '13.0.1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'antareja_base',
    ],
    # always loaded
    'data': [
        'data/cron.xml',
        'views/application_server_auth_views.xml',
        'views/menuitem.xml',
    ],

}
