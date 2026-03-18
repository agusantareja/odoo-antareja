# -*- coding: utf-8 -*-
{
    'name': "CMP ||Account || Account Move Approval",
    'summary': """Approval template for Account Module base on journal""",
    'description': """
    """,
    'author': "Agus Muhammad Ramdan",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '13.0.1',
    'depends': ['base', 'mail', 'account', 'cmp_account', 'cmp_metalindo_approval'],
    'data': [
        'data/cni_approval_template_data.xml',
        'views/account_journal_views.xml',
        'views/account_move_views.xml',
    ],
}
