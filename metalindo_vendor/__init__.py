# -*- coding: utf-8 -*-

from . import models

# We don't want to load res.city.csv and res.zipcode.csv every time we upgrade this module, since
# they contain lots of data. We will load them manually using pre_init_hook (we are using
# pre_init_hook here, instead of post_init_hook, since we need to ensure these data are loaded
# before loading data/uppercase_address_data.xml).
def _load_indonesian_cities_and_zipcodes(cr):
    from odoo import tools

    # Load the cities first...
    tools.convert_file(
        cr,
        'metalindo_vendor',
        'data/res.city.csv',
        None,
        mode='init',
        noupdate=True,
        kind='init'
    )

    # ..then the zip codes
    tools.convert_file(
        cr,
        'metalindo_vendor',
        'data/res.zipcode.csv',
        None,
        mode='init',
        noupdate=True,
        kind='init'
    )
