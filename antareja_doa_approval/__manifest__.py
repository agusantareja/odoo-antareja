# -*- coding: utf-8 -*-
{
    'name': "DOA || Approval",

    'summary': """
        Add Feature Approval Task
        """,

    'description': """
        
    """,

    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '13.0.1',

    'depends': ['base', 'mail', 'hr', 'antareja_doa', 'antareja_approval', 'antareja_approval_hr_employee'],

    # always loaded
    'data': [
        'data/approval_strategy_template_stage_data.xml',
        'views/user_delegate_views.xml'
    ],
}
