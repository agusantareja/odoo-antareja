# -*- coding: utf-8 -*-
{
    'name': "CMP || Vendor Metalindo Approval",
    'summary': """ Refactoring approval """,

    'description': """
        Custom module for account comunity version
    """,

    'author': "Agus Muhammad Ramdan",
    # 'website': "http://www.yourcompany.com",

    'category': 'Accounting',
    'version': '16.0.1.0.0',
    'depends': [
        'base',
        'antareja_base',
        'antareja_notification_whatsapp',
        'metalindo_vendor_approval',
        'cmp_account',
        'cmp_metalindo_approval',
    ],
    # always loaded
    'data': [
        'data/notification_template_data.xml',
        'data/approval_template_data.xml',
        'views/vendor_approval.xml'
    ],
    'post_init_hook': 'post_init_hook',
}
