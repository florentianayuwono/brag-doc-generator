import pytest
from bragdoc.fetchers.base import Fetcher


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        Fetcher()


def test_subclass_contract():
    class Dummy(Fetcher):
        name = "dummy"

        def enabled(self, config):
            return True

        def fetch(self, config):
            return []

    d = Dummy()
    assert d.name == "dummy"
    assert d.enabled(None) is True
    assert d.fetch(None) == []
