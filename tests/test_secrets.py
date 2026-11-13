from acbox import secrets


def test_read_key(resolver):
    key = secrets.read_key(resolver.lookup("secrets/key.pub"))
    assert key is None

    key = secrets.read_key(resolver.lookup("secrets/key"))
    assert isinstance(key, secrets.Key)


def test_lookup(resolver, tmp_path):
    key = secrets.lookup(resolver.lookup("secrets/key.pub"))
    assert key is None

    key = secrets.lookup(resolver.lookup("secrets/key"))
    assert isinstance(key, secrets.Key)

    assert key == secrets.lookup(resolver.lookup("secrets"))


def test_encrypt(resolver, tmp_path):
    key = secrets.lookup(resolver.lookup("secrets/key"))
    data = resolver.load("secrets/tomlcat.example.toml", mode="text")

    encrypted = secrets.encrypt(data, key)
    decrypted = secrets.decrypt(encrypted, key)
    assert decrypted == data
