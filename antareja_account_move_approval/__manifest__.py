# -*- coding: utf-8 -*-
{
    'name': "Account || Approval",
    'summary': """Approval template for Account Module base on journal""",
    'description': """
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.1',
    'depends': ['base', 'mail', 'account', 'antareja_approval'],
    'data': [
        'views/account_journal_views.xml',
        'views/account_move_views.xml',
    ],
}
