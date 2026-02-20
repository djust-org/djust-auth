# djust-auth

Authentication views, mixins, and OAuth integration for [djust](https://github.com/johnrtipton/djust) applications.

## Features

- **Login / Signup / Logout views** — Drop-in authentication views with customizable templates
- **LiveView mixins** — `LoginRequiredLiveViewMixin` and `PermissionRequiredLiveViewMixin` for protecting djust LiveViews
- **OAuth via django-allauth** — Optional OAuth support (GitHub, Google, GitLab, OIDC, etc.)
- **djust-admin plugin** — Dashboard widget, OAuth Providers page, and Social Accounts page for [djust-admin](https://github.com/johnrtipton/djust-admin)
- **Context processor** — Injects configured OAuth providers into templates for rendering login buttons

For a complete integration walkthrough including OIDC, dual-template-backend setup, and troubleshooting, see [docs/oidc-integration.md](docs/oidc-integration.md).

---

## Installation

```bash
# Core (login/signup/logout views + mixins)
pip install djust-auth

# With OAuth support
pip install "djust-auth[oauth]"
```

---

## Quick Setup

### 1. INSTALLED_APPS (order matters)

```python
INSTALLED_APPS = [
    # ...
    "django.contrib.sites",           # ← MUST come before allauth.socialaccount
    "djust_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # Add providers you need:
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
]

SITE_ID = 1  # Required for SocialApp credential resolution
```

> **Why `django.contrib.sites` first:** `socialaccount`'s first migration has a hard
> dependency on the `sites` migration. If `sites` is added later you get
> `InconsistentMigrationHistory`. See [docs/oidc-integration.md](docs/oidc-integration.md)
> for recovery steps.

### 2. MIDDLEWARE

`AccountMiddleware` must be **last** in the list:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # ...
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # ← LAST
]
```

Placing it in the middle causes subtle OAuth redirect loops.

### 3. Authentication backends

```python
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
```

### 4. URLs

```python
# urls.py
urlpatterns = [
    path("accounts/", include("djust_auth.urls")),   # login/logout/signup
    path("accounts/", include("allauth.urls")),       # OAuth callbacks — no namespace
]
```

Do **not** add a `namespace=` to `allauth.urls` — it breaks allauth's internal `reverse()` calls.

### 5. Migrate

```python
python manage.py migrate
```

After migrating, ensure the default `Site` object exists for `SITE_ID = 1`:

```bash
python manage.py shell -c "
from django.contrib.sites.models import Site
Site.objects.update_or_create(pk=1, defaults={'domain': 'localhost:8000', 'name': 'My App'})
"
```

---

## OAuth Provider Config

### Standard providers (GitHub / Google / GitLab)

```python
SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APP": {
            "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
            "secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        },
        "SCOPE": ["user:email"],   # ← SCOPE at provider level, NOT inside APP
    },
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        },
        "SCOPE": ["profile", "email"],
    },
}
```

### OIDC (Keycloak, etc.)

```python
SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "oidc",
                "name": os.getenv("OIDC_PROVIDER_NAME", "OIDC"),
                "client_id": os.getenv("OIDC_CLIENT_ID", ""),
                "secret": os.getenv("OIDC_CLIENT_SECRET", ""),
                "settings": {
                    "server_url": os.getenv("OIDC_SERVER_URL", ""),
                    # allauth auto-appends /.well-known/openid-configuration
                    "token_auth_method": "client_secret_basic",
                },
            }
        ]
    }
}
```

Callback URI to register: `http://<host>/accounts/oidc/login/callback/`

---

## Templates

### Context processor

Add `social_auth_providers` to your **Django** template backend (not the djust Rust backend):

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # ...
                "djust_auth.social.social_auth_providers",  # injects oauth_providers
            ],
        },
    },
]
```

### Provided templates (via APP_DIRS)

- `djust_auth/includes/oauth_buttons.html` — reusable OAuth button list
- `djust_auth/admin/providers.html` — admin OAuth Providers page
- `djust_auth/admin/social_accounts.html` — admin Social Accounts page
- `djust_auth/admin/widgets/auth_summary.html` — admin dashboard widget

### Templates you must create

In your project's templates dir, create `djust_auth/login.html` and `djust_auth/signup.html`.

Minimal `login.html`:

```html
{% if oauth_providers %}
  {% for provider in oauth_providers %}
    <a href="{{ provider.login_url }}?next={{ request.GET.next|default:'/' }}">
      {{ provider.icon }} Continue with {{ provider.label }}
    </a>
  {% endfor %}
{% endif %}
<form method="post">{% csrf_token %}
  <input name="username" type="text">
  <input name="password" type="password">
  <button type="submit">Sign In</button>
</form>
```

`oauth_providers` items: `name`, `label`, `icon` (SVG wrapped in `mark_safe()` — render unescaped), `login_url`.
Built-in icons for GitHub, Google, GitLab.

Or use the included partial:

```html
{% include "djust_auth/includes/oauth_buttons.html" %}
```

---

## LiveView Mixins

```python
from djust_auth.mixins import LoginRequiredLiveViewMixin, PermissionRequiredLiveViewMixin
from djust import LiveView

# Redirect anonymous users to login with ?next=<current-path>
class MyProtectedView(LoginRequiredLiveViewMixin, LiveView):
    template_name = "my_app/protected.html"

# Raise 403 if user lacks permission
class MyAdminView(PermissionRequiredLiveViewMixin, LiveView):
    template_name = "my_app/admin.html"
    permission_required = "my_app.can_manage"

# Combine: redirect anonymous, 403 for authenticated-but-unauthorized
class StrictView(LoginRequiredLiveViewMixin, PermissionRequiredLiveViewMixin, LiveView):
    template_name = "my_app/strict.html"
    permission_required = "my_app.can_manage"
    # LoginRequired must come first in MRO so anon users get a redirect, not a 403
```

Both mixins intercept at `dispatch()` before `mount()` runs, so no LiveView state is
initialized for unauthorized users.

---

## djust-admin Plugin

If [djust-admin](https://github.com/johnrtipton/djust-admin) is installed, djust-auth
automatically registers a plugin via autodiscovery. No extra configuration needed.

**Dashboard widget** (`AuthSummaryWidget`):
- Total users, new this week, staff, superusers
- OAuth user count and configured provider count

**OAuth Providers page** (`/admin/auth/providers`):
- Callback URLs, masked client IDs, scope validation
- Per-provider usage stats and settings snippets
- Warning if `SCOPE` is misplaced inside `APP`

**Social Accounts page** (`/admin/auth/accounts`, requires `allauth.socialaccount`):
- LiveView table — searchable, sortable, filterable by provider, paginated

The `SocialAccount` model is also registered with `DjustModelAdmin` automatically.

---

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `InconsistentMigrationHistory` | `allauth.socialaccount` before `django.contrib.sites` | Move `django.contrib.sites` above `allauth.socialaccount` |
| OAuth login fails silently | `SITE_ID` not set or `django_site` pk=1 missing | Set `SITE_ID = 1`, run `update_or_create` shell command |
| OAuth redirect loop | `AccountMiddleware` not last | Move after `XFrameOptionsMiddleware` |
| `NoReverseMatch` for allauth URLs | `allauth.urls` included with `namespace=` | Remove `namespace=` |
| `SCOPE` silently ignored | `SCOPE` inside `APP` dict | Move `SCOPE` up one level |
| `oauth_providers` always empty | Context processor on wrong template backend | Add only to `DjangoTemplates` backend, not djust Rust backend |

---

## Development

```bash
# Install dev dependencies
pip install -e ".[test,oauth]"

# Run tests
pytest
```

---

## Local OAuth Testing

### GitHub
1. Go to https://github.com/settings/developers → "New OAuth App"
2. Callback URL: `http://localhost:PORT/accounts/github/login/callback/`
3. Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in your `.env`

### Google
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth client ID (Web application)
3. Redirect URI: `http://localhost:PORT/accounts/google/login/callback/`
4. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your `.env`

### Keycloak (OIDC)
1. Create a client in your realm with "Standard flow" enabled
2. Redirect URI: `http://localhost:PORT/accounts/oidc/login/callback/`
3. Set `OIDC_SERVER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` in your `.env`
