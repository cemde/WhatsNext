import abc


class BaseFormatter(abc.ABC):
    pass


class TestBaseFormatter:
    def test_base_formatter(self):
        assert issubclass(BaseFormatter, abc.ABC)
