
import logging
import inspect
from functools import wraps

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


def save_call_method(obj, method_name, **kw):
    """
    Memanggil method pada object secara aman.
    Deprecated gunakan safe_call_method
    """
    return safe_call_method(obj, method_name, **kw)
    # if obj is None or not method_name or not isinstance(method_name, str):
    #     return None
    #
    # method = getattr(obj, method_name, None)
    # if not callable(method):
    #     raise AttributeError(f"Callable method '{method_name}' not found on {obj}")
    #
    # if not hasattr(obj, method_name):
    #     raise AttributeError(f"Method {method_name} not found")
    #
    # method = getattr(obj, method_name)
    #
    # # cek apakah method menerima **kw
    # signature = inspect.signature(method)
    # has_var_keyword = any(
    #     p.kind == p.VAR_KEYWORD
    #     for p in signature.parameters.values()
    # )
    #
    # if has_var_keyword:
    #     # method menerima **kwargs
    #     return method(**kw)
    # else:
    #     # method tidak menerima **kwargs
    #     # Hanya kirim parameter yang cocok
    #     valid_params = {
    #         name: kw[name]
    #         for name in signature.parameters.keys()
    #         if name in kw
    #     }
    #     return method(**valid_params)


def safe_call_method(obj, method_name, *args, **kwargs):
    """
    Memanggil method pada object secara aman.

    - method optional
    - method_name harus string
    - method harus callable
    - args disesuaikan dengan signature
    """

    if not obj or not method_name or not isinstance(method_name, str):
        return None

    if not hasattr(obj, method_name):
        raise AttributeError(f"Method {method_name} not found")

    method = getattr(obj, method_name, None)
    if not callable(method):
        raise AttributeError(f"Callable method '{method_name}' not found on {obj}")

    # === signature aware ===
    sig = inspect.signature(method)
    params = sig.parameters

    final_args = []
    final_kwargs = {}

    for name, p in params.items():
        if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD
        ):
            if args:
                final_args.append(args[0])
                args = args[1:]
            elif name in kwargs:
                final_args.append(kwargs[name])
            elif p.default is not inspect.Parameter.empty:
                pass
            else:
                raise TypeError(f"Missing required argument: {name}")

        elif p.kind == inspect.Parameter.VAR_POSITIONAL:
            final_args.extend(args)
            args = ()

        elif p.kind == inspect.Parameter.KEYWORD_ONLY:
            if name in kwargs:
                final_kwargs[name] = kwargs[name]
            elif p.default is inspect.Parameter.empty:
                raise TypeError(f"Missing keyword-only argument: {name}")

        elif p.kind == inspect.Parameter.VAR_KEYWORD:
            final_kwargs.update(kwargs)

    return method(*final_args, **final_kwargs)


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


def call_retry(callback_error_method_name=None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            _logger.info(f"Function in {func.__qualname__}")
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                _logger.error(f"Error in {func.__qualname__}: {str(e)}", exc_info=True)
                error_message = str(e)
                res_method = func.__name__
                api_call_retry_id = self.env.context.get('__api_call_retry_id')
                if api_call_retry_id:
                    api_call_retry = self.env['api.call.retry'].browse(api_call_retry_id)
                else:
                    api_call_retry = self.env['api.call.retry']

                api_call_retry.need_retry(
                    self._name, self.id, res_method=res_method,
                    error_message=error_message, param_args=args, param_kwargs=kwargs
                )

                if callback_error_method_name and have_method(self, callback_error_method_name):
                    return safe_call_method(self, callback_error_method_name, **{
                        'args': args,
                        'method_name': res_method,
                        'exception': e,
                        'kwargs': kwargs
                    })
                return

        return wrapper

    return decorator
