
import inspect


def get_callable_method(obj, method):
    return obj and method and hasattr(obj, method) and callable(getattr(obj, method))


def is_callable_method(model, method):
    return bool(model and method and hasattr(model, method) and callable(getattr(model, method)))


def has_kwargs(func):
    sig = inspect.signature(func)
    return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
