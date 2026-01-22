# -*- coding: utf-8 -*-
{
    'name': "CMP || Employee",
    'summary': """
         Modul ini integrasi ke applikasi app_intra_cerindocorp
         
         Data 
         """,
    'description': """
        Data dari modul HR akan di bill dari hr.ceridocorp.id via intra.creindocorp.id,
        bila ingin menambahkan field tambahkan di cmp_hr
        WARNING:
        Jangan depend dan menambahkan field business di module ini.
    """,
    'author': "Agus Muhammad Ramdan",
    'category': 'Accounting',
    'version': '16.0.1.0.1',
    'depends': [
        'base',
        'hr',
        'cmp_hr',
        'antareja_integration_sync',
        'antareja_integration_app_intra_cerindocorp',
        'cmp_account_ecv',
    ],
    # always loaded
    'data': [
        'security/res_groups.xml',
        'data/external_server_sync_data.xml',
        'data/hr_employee_data.xml',
        'data/hr_department_data.xml',
        'data/res_partner_employee_data.xml',
        'data/hr_job_data.xml',
    ],
}
