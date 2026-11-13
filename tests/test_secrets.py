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
    data = resolver.load("tomlcat.example.toml", mode="text")

    encrypted = secrets.encrypt(data, key)
    decrypted = secrets.decrypt(encrypted, key)
    assert decrypted == data


def test_secretpath():
    path = secrets.SecretPath("blah", key=11)
    assert path.key == 11

    path1 = path.expanduser()
    assert path.key == 11 and path1.key == 11

    path2 = path1.resolve()
    assert path.key == 11 and path1.key == 11 and path2.key == 11
