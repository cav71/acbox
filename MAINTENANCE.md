## Release

1. get version: `version=$(awk -F= '/^version\s*/{print $2}' pyproject.toml | tr -d '" ')`
2. git tag: `git tag -m "release $version" v$version"`
3. push: `git push origin v$version`
4. **update pyproject.toml** with a new version!

## Cleanup
