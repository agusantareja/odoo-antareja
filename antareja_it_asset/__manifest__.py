# -*- coding: utf-8 -*-
{
    'name': "Antareja || IT Asset",
    'summary': """ Integarsi Odoo dengan snipe asset """,
    'description': """
        Long description of module's purpose
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base','hr'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/hr_employee_view.xml',
        'views/res_config_settings_views.xml',
    ],
}
