# -*- coding: utf-8 -*-
{
    'name': "Bill Vendor || Approval",
    'summary': """Add Feature Approval Task""",
    'description': """
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.1',
    'depends': [
        'base', 'mail', 'account',
        'antareja_approval',
        'antareja_account_move_approval',
        'antareja_approval_matrix_tiered',
    ],

    # always loaded
    'data': [
        'data/approval_strategy_template_data.xml',
        #'views/account_move_views.xml'
    ],
}
