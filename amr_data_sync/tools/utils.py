
import inspect


def get_callable_method(obj, method):
    try:
        return hasattr(obj, method) and callable(getattr(obj, method))
    except Exception:
        return False


def is_callable_method(model, method):
    return get_callable_method(model, method)


def has_kwargs(func):
    sig = inspect.signature(func)
    return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
