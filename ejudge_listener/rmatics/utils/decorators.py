import functools
import warnings


def deprecated(new_name=None):
    """Deprecate something."""

    def decorator(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            if new_name:
                message = (
                    f'{func.__module__}.{func.__name__} is deprecated. Please '
                    f'replace it by {new_name}'
                )
            else:
                message = (
                    f'{func.__module__}.{func.__name__} is deprecated, but it '
                    f'doesn\'t have any replacement yet.'
                )

            warnings.simplefilter('always', DeprecationWarning)
            warnings.warn(message, category=DeprecationWarning, stacklevel=2)
            warnings.simplefilter('default', DeprecationWarning)
            return func(*args, **kwargs)

        return new_func

    return decorator


def do_not_execute(return_value=None, raised_exception=None):
    """ This decorator can be useful for deprecating some code
        Ordinary case when you removed `backend` which used by function
        but function still called somewhere.
        This decorator is usable only for development.
        So basic usage is:

        Usage
        ---------
        @do_not_execute(return_value='my_string')
        def never_should_called(a, b):
            ...
            <code which never executed>
            ...
            return 'some_string'

        never_should_called(1, 2) -> 'my_string'

    """

    def decorator(func):
        @functools.wraps(func)
        def new_func(*_, **__):
            if raised_exception:
                raise raised_exception
            return return_value

        doc = 'This function is marked as do_not_execute ' \
              f'and always returns {return_value}\n\n' \
              f'{new_func.__doc__ or ""}'
        new_func.__doc__ = doc
        return new_func

    return decorator
