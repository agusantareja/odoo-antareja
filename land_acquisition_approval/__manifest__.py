# -*- coding: utf-8 -*-

{
    'name'          : "Land Acquisition Approval",
    'description'   : """
        - Land Acquisition Approval
    """,
    'category'      : 'Inventory',
    'depends'       : [
        'base',
        'mail',
        'land_acquisition',
        'antareja_base',
    ],
    "installable"   : True,
    'data': [
        'views/land_acquisition_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
