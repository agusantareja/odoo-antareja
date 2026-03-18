# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


def ignore_delegated_user_context(func):
    def wrapper(self, *args, **kwargs):
        proxy_activate = self.env.context.get('__ignore_delegated_user_proxy_activate')
        if not proxy_activate:
            context = dict(self.env.context, __ignore_delegated_user_proxy_activate=True)
            self = self.with_context(context)
        result = func(self, *args, **kwargs)
        return result

    return wrapper


def param_transaction_object(func):
    def wrapper(self, *args, **kwargs):
        transaction_object = kwargs.get('transaction_object') or self.get_transaction_object()
        kwargs['transaction_object'] = transaction_object
        result = func(self, *args, **kwargs)
        return result

    return wrapper


def ensure_create_tuples_many2one(items):
    """
    Mengubah item menjadi format relasi Many2one/O2M/M2M untuk Odoo,
    dengan pengecekan agar tidak mengkonversi tuple yang sudah benar.

    :param items: list of dict, int, atau tuple (0, 0, {...})
    :return: list of tuple relasi Odoo
    """
    result = []
    for item in items:
        if (isinstance(item, tuple)
                and len(item) == 3
                and item[0] == 0
                and item[1] == 0
                and isinstance(item[2], dict)):
            # Sudah dalam format (0, 0, {...}) → biarkan
            result.append(item)
        elif isinstance(item, dict):
            # Belum diformat → buat tuple create
            result.append((0, 0, item))
        elif isinstance(item, int):
            # ID record yang sudah ada → link dengan (4, id, 0)
            result.append((4, item, 0))
        else:
            raise ValueError(f"Unsupported item type or format: {item}")
    return result


def get_strategy_from_field_name(field_names):
    """Mengambil strategy dari nama field dengan pola stage_*_id.
    Bisa menerima string tunggal atau list of string.
    """
    import re

    # Pastikan selalu berupa list untuk diproses
    if isinstance(field_names, str):
        field_names = [field_names]

    strategies = []
    for fname in field_names:
        match = re.match(r"^stage_(.+)_id$", fname)
        if match:
            strategies.append(match.group(1))

    return strategies


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


def render_jinja(template_string, context):
    from jinja2 import Environment, BaseLoader
    env = Environment(
        loader=BaseLoader(),
        autoescape=False,
        variable_start_string='${',  # ubah pembuka variable
        variable_end_string='}',  # ubah penutup variable
        block_start_string='<%',  # ubah pembuka block (if/for dsb)
        block_end_string='%>',  # ubah penutup block
        comment_start_string='<#',  # ubah pembuka komentar
        comment_end_string='#>'  # ubah penutup komentar
    )
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
    if hasattr(rec_object, "requester_id"):
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


def compare_model_fields(field_a, field_b, env):
    def to_model_id(field):
        if hasattr(field, "_name"):  # Recordset (many2one/browse)
            if not field:  # Recordset kosong
                return None, None
            return field._name, field.id

        if isinstance(field, str):  # Reference string
            if ',' not in field:
                return None, None
            model, rec_id = field.split(',', 1)
            if not rec_id.isdigit():
                return None, None
            return model, int(rec_id)

        return None, None

    model_a, id_a = to_model_id(field_a)
    model_b, id_b = to_model_id(field_b)

    if not model_a or not model_b:
        return False

    return (model_a == model_b) and (id_a == id_b)


def get_email_template_approval_id(rec_object):
    try:
        if hasattr(rec_object, "email_template_approval_id"):
            return rec_object.email_template_approval_id.id
    except Exception as e:
        _logger.error("Error getting notification approval email template ID: %s", e)
    return None


def get_email_template_rejection_id(rec_object):
    """
    Method to get the notification approval email template ID.
    This method should be implemented in the inheriting model.
    """
    try:
        if hasattr(rec_object, "email_template_rejection_id"):
            return rec_object.email_template_rejection_id.id
    except Exception as e:
        _logger.error("Error getting notification approval email template ID: %s", e)

    return None


def get_mail_bot_template_approval_id(rec_object):
    try:
        if hasattr(rec_object, "mail_bot_template_approval_id"):
            return rec_object.mail_bot_template_approval_id.id
    except Exception as e:
        _logger.error("Error getting notification approval mail bot template ID: %s", e)
    return None


def get_mail_bot_template_rejection_id(rec_object):
    """
    Method to get the notification approval email template ID.
    This method should be implemented in the inheriting model.
    """
    try:
        if hasattr(rec_object, "mail_bot_template_rejection_id"):
            return rec_object.mail_bot_template_rejection_id.id
    except Exception as e:
        _logger.error("Error getting notification approval mail bot template ID: %s", e)

    return None


def get_whatsapp_template_approval_id(rec_object):
    try:
        if hasattr(rec_object, "whatapp_template_approval_id"):
            return rec_object.whatapp_template_approval_id.id
    except Exception as e:
        _logger.error("Error getting notification approval whatapp template ID: %s", e)
    return None


def get_whatsapp_template_rejection_id(rec_object):
    """
    Method to get the notification approval email template ID.
    This method should be implemented in the inheriting model.
    """
    try:
        if hasattr(rec_object, "whatapp_template_rejection_id"):
            return rec_object.whatapp_template_rejection_id.id
    except Exception as e:
        _logger.error("Error getting notification approval whatapp template ID: %s", e)

    return None
