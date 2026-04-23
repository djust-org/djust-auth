# Migrating from `djust-auth` to `djust.auth`

This repo is deprecated. All functionality is now in the `djust` core package.

## 1. Replace the install

```diff
- pip install djust-auth
+ pip install djust
```

## 2. Update imports

Grep-replace the top-level package name:

```bash
# On POSIX:
grep -rl 'djust_auth' . | xargs sed -i '' 's/djust_auth/djust.auth/g'   # macOS
grep -rl 'djust_auth' . | xargs sed -i     's/djust_auth/djust.auth/g'   # Linux
```

## 3. Import mapping

| Before                              | After                         |
| ----------------------------------- | ----------------------------- |
| `from djust_auth import X`          | `from djust.auth import X`    |
| `import djust_auth`                 | `from djust import auth`      |
| `'djust_auth'` in `INSTALLED_APPS`  | `'djust.auth'`                |

All public names exported by `djust_auth` are re-exported from `djust.auth` with the same signatures.

## 4. Remove the old dep

Once imports are migrated and tests pass, remove `djust-auth` from your `pyproject.toml` / `requirements.txt`. The shim package depends on `djust>=0.5.6rc1` so djust is already installed.
