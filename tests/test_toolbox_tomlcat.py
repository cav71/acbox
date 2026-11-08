import pytest

from acbox.toolbox import tomlcat


def test_tget(resolver):
    data = resolver.load("tomlcat.example.toml")
    assert "a secret key" == tomlcat.tget(data, "system.secret_key")

    assert {"SECRET_KEY": "a secret key"} == tomlcat.tget(data, "system")


def test_tgets(resolver):
    data = resolver.load("tomlcat.example.toml")

    assert "a secret key" == tomlcat.tgets(data, "system.secret_key")
    assert tomlcat.tgets(data, "system.secret_key") == tomlcat.tgets(data, ["system.secret_key"])

    assert {"SECRET_KEY": "a secret key"} == tomlcat.tgets(data, "system")
    assert tomlcat.tgets(data, "system") == tomlcat.tgets(data, ["system"])

    pytest.raises(RuntimeError, tomlcat.tgets, data, ["system.secret_key", "system"])

    assert {
        "pghost": "127.0.0.1",
        "pgport": 5432,
        "pguser": "postgres-user",
        "pgpassword": "postgres-pass",
        "pgdatabase": "postgres-db",
    } == tomlcat.tgets(data, ["database"])
    assert tomlcat.tgets(data, "database") == tomlcat.tgets(data, ["database"])

    assert {
        "SECRET_KEY": "a secret key",
        "pghost": "127.0.0.1",
        "pgport": 5432,
        "pguser": "postgres-user",
        "pgpassword": "postgres-pass",
        "pgdatabase": "postgres-db",
    } == tomlcat.tgets(data, ["system", "database"])
