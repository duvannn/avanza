"""
decorators.py
~~~~~~~~~~~~~

Decorators used in avanza.py.

"""

from exceptions import AuthRequired
from functools import wraps

def auth_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.username is None and self.password is None:
            raise AuthRequired("This method requires authenthication!"
                               "Enter your credentials.")
        return func(self, *args, **kwargs)
    return wrapper
