"""
Private method in subclasses
"""

__all__ = ["Klass"]

class _PrivateKlass:
    def private_method(self):
        """
        >>> 2 / 3
        0.667
        """
        pass


class Klass(_PrivateKlass):
    def public_method(self):
        """
        >>> 3 / 4
        0.74
        """
        pass
