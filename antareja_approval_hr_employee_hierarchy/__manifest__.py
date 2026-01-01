# -*- coding: utf-8 -*-
{
    'name': "Approval hr employee Hierarchy",

    'summary': """
        Add Feature Approval
        """,

    'description': """
        
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '13.0.1.0.0',

    'depends': ['base', 'mail', 'hr', 'antareja_base'],

    # always loaded
    'data': [
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
    ],
}
