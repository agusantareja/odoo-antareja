# -*- coding: utf-8 -*-

{
    'name'          : "Leave Compensatory Request|| Integration HCIS",
    'description'   : """
        - Leave Integration to HCIS 
    """,
    'category'      : 'HR',
    'depends'       : ['base','leave', 'antareja_base',],
    "installable"   : True,
    'data': [
        'views/leave_compensatory_request_views.xml',
    ],

}
