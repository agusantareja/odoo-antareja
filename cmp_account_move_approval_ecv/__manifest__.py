# -*- coding: utf-8 -*-
{
    'name': "ECV - Add Feature Approval Task",
    'summary': """Add Feature Approval Task""",
    'description': """
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.1',
    'depends': [
        'base', 'mail', 'account',
        'cmp_account',
        'cmp_account_move_approval',
        'antareja_approval',
        'antareja_account_move_approval',
        'antareja_approval_matrix_tiered',
    ],

    # always loaded
    'data': [
        'data/approval_strategy_template_data.xml',
    ],
}
