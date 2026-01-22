{
    'name': "Allowed Cost Center",
    'author': "Agus Muhammad Ramdan",
    'category': 'Accounting',
    'description': """
    seharusnya addons allowed_cost_center tidak menjadi base modul
    tidak depend ke modul bisnis
    
    'metalindo_direct_charge',
    'tender',
    
    Notes:
    Addosn allowed_cost_center ini di perlukan untuk
    """,

    'version': '1.0',
    'sequence': 2,
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'analytic',
    ],
    # always loaded
    'data': [
        'views/res_users.xml',
    ],
}
