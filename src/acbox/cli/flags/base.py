import argparse


class ArgumentTypeBase:
    class _NA:
        pass

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._default = self._NA
        self.__name__ = self.__class__.__name__

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        if value is ArgumentTypeBase._NA:
            self._default = ArgumentTypeBase._NA
        else:
            self._default = self._validate(value)
        return self._default

    def __call__(self, txt):
        self._value = None
        self._value = self._validate(txt)
        return self

    @property
    def value(self):
        return getattr(self, "_value", self.default)

    def _validate(self, value):
        try:
            return self.validate(value)
        except argparse.ArgumentTypeError as exc:
            if not hasattr(self, "_value"):
                raise RuntimeError(f"cannot use {value=} as default: {exc.args[0]}")
            raise

    def validate(self, txt):
        raise NotImplementedError("need to implement the .validate(self, txt)  method")
