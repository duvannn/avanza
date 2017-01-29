"""
exceptions.py.
~~~~~~~~~~~~~~

Custom exceptions to raise in avanza.py

"""


class AuthError(Exception):
    """Authenthication failed due to incorrect credentials"""

class AuthRequired(Exception):
    """No authenthication credentials were specified"""
