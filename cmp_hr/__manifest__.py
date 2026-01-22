# -*- coding: utf-8 -*-
{
    'name': "CMP || HR",
    'summary': """
        Custom module for account module compatible with """,
    'description': """
        Custom module for account comunity version
    """,
    'author': "Agus Muhammad Ramdan",
    'category': 'HR',
    'version': '16.0.1.0.0',
    'depends': [
        'base',
        'hr',
    ],
    # always loaded
    'data': [
        'security/res_groups.xml',
        'data/hr_job_data.xml',
    ],
}
