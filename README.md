# djust-auth

Authentication views, mixins, and OAuth integration for [djust](https://github.com/johnrtipton/djust) applications.

## Features

- **Login / Signup / Logout views** — Drop-in authentication views with customizable templates
- **LiveView mixins** — `LoginRequiredLiveViewMixin` and `PermissionRequiredLiveViewMixin` for protecting djust LiveViews
- **OAuth via django-allauth** — Optional OAuth support (GitHub, Google, GitLab, etc.) with a single `pip install`
- **djust-admin plugin** — Dashboard widget and OAuth provider management page for [djust-admin](https://github.com/johnrtipton/djust-admin)
- **Context processor** — Injects configured OAuth providers into templates for rendering login buttons

## Installation

```bash
# Core (login/signup/logout views + mixins)
pip install djust-auth

# With OAuth support
pip install "djust-auth[oauth]"
```

Add to your Django settings:

```python
INSTALLED_APPS = [
    # ...
    "djust_auth",
]
```

Include URLs in your project:

```python
# urls.py
urlpatterns = [
    path("accounts/", include("djust_auth.urls")),
]
```

## OAuth Setup

### 1. Install with OAuth extra

```bash
pip install "djust-auth[oauth]"
```

### 2. Add allauth to your Django settings

```python
INSTALLED_APPS = [
    # ...
    "djust_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # Add providers you need:
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
]

MIDDLEWARE = [
    # ... after AuthenticationMiddleware:
    "allauth.account.middleware.AccountMiddleware",
    # ...
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
```

### 3. Include allauth URLs at the project level

allauth URLs must be included **outside** the djust_auth namespace so allauth's internal URL resolution works:

```python
# urls.py
urlpatterns = [
    path("accounts/", include("djust_auth.urls")),
    path("accounts/", include("allauth.urls")),  # Must be separate, not nested
    # ...
]
```

### 4. Configure providers

```python
SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APP": {
            "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
            "secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        }
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

### 5. Add OAuth buttons to your login template

Add the context processor to inject provider data:

```python
TEMPLATES = [{
    "OPTIONS": {
        "context_processors": [
            # ...
            "djust_auth.social.social_auth_providers",
        ],
    },
}]
```

Then include the buttons in your login/signup templates:

```html
{% if oauth_providers %}
<div class="divider">or continue with</div>
{% include "djust_auth/includes/oauth_buttons.html" %}
{% endif %}
```

### 6. Run migrations

```bash
python manage.py migrate
```

## djust-admin Plugin

If [djust-admin](https://github.com/johnrtipton/djust-admin) is installed, djust-auth automatically registers a plugin via autodiscovery that provides:

- **Authentication widget** on the admin dashboard (user count, recent signups, staff count, OAuth provider count)
- **OAuth Providers page** at `/djust-admin/auth/providers/` showing provider status and linked account counts

No extra configuration needed — just have both `djust_auth` and `djust_admin` in `INSTALLED_APPS`.

## Mixins

```python
from djust_auth.mixins import LoginRequiredLiveViewMixin, PermissionRequiredLiveViewMixin

class MyProtectedView(LoginRequiredLiveViewMixin, LiveView):
    template_name = "my_app/protected.html"

class MyAdminView(PermissionRequiredLiveViewMixin, LiveView):
    template_name = "my_app/admin.html"
    permission_required = "my_app.can_manage"
```

## Development

```bash
# Install dev dependencies
pip install -e ".[test,oauth]"

# Run tests
pytest
```

## Local OAuth Testing

### GitHub

1. Go to https://github.com/settings/developers > "New OAuth App"
2. Set callback URL: `http://localhost:PORT/accounts/github/login/callback/`
3. Add `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` to your `.env`

### Google

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth client ID (Web application)
3. Add redirect URI: `http://localhost:PORT/accounts/google/login/callback/`
4. Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to your `.env`
