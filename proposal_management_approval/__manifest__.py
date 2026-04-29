# -*- coding: utf-8 -*-

{
    'name'          : "Proposal Management Approval",
    'description'   : """
        - Proposal Management Approval
    """,
    'category'      : 'Inventory',
    'depends'       : [
        'base',
        'mail',
        'proposal_management',
        'antareja_base',
    ],
    "installable"   : True,
    'data': [
        'views/proposal_management_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
