# -*- coding: utf-8 -*-

from odoo import models

class ResourceResource(models.Model):
    _inherit = "resource.resource"

    def prepare_input_dict(self, item, input_dict=None, sync_strategy=None, **kwargs):
        """ Process data from external source to create or update res.partner as employee
                :param item: dict from external source
                :param sync_strategy: external.data.sync.strategy record
                :param data_sync: external.data.sync record
                :param kwargs: other parameter from external source
                :return: res.partner record
                """
        input_dict = input_dict or {}
        return input_dict

    def external_data_sync_done(self, **kwargs):
        # dipanggil saat done
        # self.create_user()
        # self.create_tapping()
        pass
