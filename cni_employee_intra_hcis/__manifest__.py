# -*- coding: utf-8 -*-

{
    'name': "Employee Intra || Integration hcis",
    'description': """
        - Integration to HCIS 
    """,
    'category': 'HR',
    'depends': ['base', 'cni_employee_intra', 'antareja_integration_sync', 'antareja_integration_app_hr_cerindocorp'],
    "installable": True,
    'data': [
        'data/external_server_sync_data.xml',
        'data/resource_resource_data.xml',
        'data/hr_department_data.xml',
        'data/hr_job_data.xml',
        'data/hr_employee_data.xml',
    ],
}
