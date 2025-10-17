# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

_logger = __import__('logging').getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


def render_jinja(template_string, context):
    from jinja2 import Environment, BaseLoader
    env = Environment(loader=BaseLoader(), autoescape=False)
    template_jinja = env.from_string(template_string)
    return template_jinja.render(context)


def to_integer(value):
    """
    Convert a value to an integer if it is not None.
    If the value is None, return None.
    """
    if value is None:
        return None
    if value is False:
        return False

    if value:
        try:
            return int(value)
        except (ValueError, TypeError):
            if isinstance(value, models.BaseModel):  # jika recordset
                return value.id

    return value


def get_transaction_link_url(rec_object):
    if "transaction_link_url" in rec_object:
        return rec_object['transaction_link_url']
    elif have_method(rec_object, "get_transaction_link_url"):
        return rec_object.get_transaction_link_url()
    return None


def get_requester_id(rec_object):
    if not rec_object:
        return None
    if hasattr(rec_object,"requester_id"):
        return rec_object.requester_id.id
    elif have_method(rec_object, "get_requester_id"):
        return rec_object.get_requester_id()
    return None


def get_transaction_menu_id(rec_object):
    if "transaction_menu_id" in rec_object:
        return rec_object['transaction_menu_id']
    elif have_method(rec_object, "get_transaction_menu_id"):
        return rec_object.get_transaction_menu_id()
    return None


def get_menu_id(self, rec_object):
    """
    Method to get the company ID of the record.
    This method should be implemented in the inheriting model.
    """
    if "menu_id" in rec_object:
        return rec_object['menu_id']
    elif have_method(rec_object, "get_menu_id"):
        return rec_object.get_menu_id()
    return None


def get_company_id(rec_object):
    if "company_id" in rec_object:
        return rec_object['company_id']
    elif have_method(rec_object, "get_company_id"):
        return rec_object.get_company_id()
    return None
