
import logging

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


import inspect


def save_call_method(obj, method_name, **kw):
    if not obj:
        return None

    if not method_name:
        return None

    if not hasattr(obj, method_name):
        raise AttributeError(f"Method {method_name} not found")

    method = getattr(obj, method_name)

    # cek apakah method menerima **kw
    signature = inspect.signature(method)
    has_var_keyword = any(
        p.kind == p.VAR_KEYWORD
        for p in signature.parameters.values()
    )

    if has_var_keyword:
        # method menerima **kwargs
        return method(**kw)
    else:
        # method tidak menerima **kwargs
        # Hanya kirim parameter yang cocok
        valid_params = {
            name: kw[name]
            for name in signature.parameters.keys()
            if name in kw
        }
        return method(**valid_params)


def convert_to_tuple_create(input):
    if isinstance(input, tuple):
        return input
    if isinstance(input, dict):
        return (0, 0, input)


def ensure_dict(input):
    if isinstance(input, dict):
        return input
    else:
        return input.prepare_line_dict()


def ensure_list_create(record_list):
    return [ensure_dict(rec) for rec in record_list]
