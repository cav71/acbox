from acbox import secrets


def test_read_key(resolver):
    key = secrets.read_key(resolver.lookup("secrets/key.pub"))
    assert key is None

    key = secrets.read_key(resolver.lookup("secrets/key"))
    assert isinstance(key, secrets.Key)


def test_lookup(resolver):
    key = secrets.lookup(resolver.lookup("secrets/key.pub"))
    assert key is None

    key = secrets.lookup(resolver.lookup("secrets/key"))
    assert isinstance(key, secrets.Key)

    assert key == secrets.lookup(resolver.lookup("secrets"))


def test_encrypt(resolver):
    key = secrets.lookup(resolver.lookup("secrets/key"))
    data = resolver.load("tomlcat.example.toml", mode="text")

    encrypted = secrets.encrypt(data, key)
    decrypted = secrets.decrypt(encrypted, key)
    assert decrypted == data


def test_roundtrip(resolver, tmp_path):
    key = secrets.lookup(resolver.lookup("secrets/key"))
    path = resolver.lookup("tomlcat.example.toml")
    assert not secrets.Key.is_encrypted(path)

    # encrypt
    encrypted = tmp_path / "encrypted.toml"
    secrets.encrypt(path.read_text(), key, encrypted)
    assert secrets.Key.is_encrypted(encrypted)
    assert encrypted.read_text() != path.read_text()

    # verify decrypted content
    found = secrets.decrypt(encrypted.read_bytes(), key)
    assert found == path.read_text()


def test_secretpath():
    path = secrets.SecretPath("blah", key=11)
    assert path.key == 11

    path1 = path.expanduser()
    assert path.key == 11 and path1.key == 11

    path2 = path1.resolve()
    assert path.key == 11 and path1.key == 11 and path2.key == 11
