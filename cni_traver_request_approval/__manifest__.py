# -*- coding: utf-8 -*-

{
    'name' : "Travel Request Approval",
    'description' : """- Travel Request""",
    'category' : 'HR',
    'depends' : ['cni_travel_request', 'antareja_base',],
    "installable" : True,
    'data': [
        'views/travel_request_views.xml'
    ],
    'post_init_hook': 'post_init_hook',
}
