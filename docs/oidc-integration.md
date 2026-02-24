# djust-auth + django-allauth OIDC — Integration Guide

Complete integration reference for `djust-auth` and `django-allauth` OIDC.

---

## Quick-Start Checklist

1. [Install packages](#1-installation)
2. [Add apps in the right order](#2-installed_apps-order-matters) — `django.contrib.sites` before `allauth.socialaccount`
3. [Add `AccountMiddleware` last](#3-middleware-accountmiddleware-goes-last)
4. [Run migrations in order](#4-migration-checklist)
5. [Configure core auth settings + `SITE_ID = 1`](#5-core-auth-settings)
6. [Configure OIDC or OAuth2 providers](#6-oidc-provider-config)
7. [Wire URLs at `accounts/`](#8-url-routing) — both `djust_auth.urls` and `allauth.urls`
8. [Set up template backends](#10-template-backends)
9. [Create `login.html` and `signup.html`](#11-templates-provided-vs-must-create)
10. [Protect LiveViews with mixins](#12-auth-mixins)
11. [Verify with curl](#15-verification)

---

## Table of Contents

- [Part 1: Setup](#part-1-setup)
  - [1. Installation](#1-installation)
  - [2. INSTALLED_APPS (order matters)](#2-installed_apps-order-matters)
  - [3. MIDDLEWARE (AccountMiddleware goes last)](#3-middleware-accountmiddleware-goes-last)
  - [4. Migration Checklist](#4-migration-checklist)
- [Part 2: Configuration](#part-2-configuration)
  - [5. Core Auth Settings](#5-core-auth-settings)
  - [6. OIDC Provider Config](#6-oidc-provider-config)
  - [7. Standard OAuth2 Providers (GitHub / Google / GitLab)](#7-standard-oauth2-providers-github--google--gitlab)
  - [8. URL Routing](#8-url-routing)
  - [9. Environment Variables](#9-environment-variables)
- [Part 3: Templates](#part-3-templates)
  - [10. Template Backends](#10-template-backends)
  - [11. Templates: Provided vs. Must-Create](#11-templates-provided-vs-must-create)
- [Part 4: Protecting djust LiveViews](#part-4-protecting-djust-liveviews)
  - [12. Auth Mixins](#12-auth-mixins)
- [Part 5: Admin Integration](#part-5-admin-integration)
  - [13. djust Admin Plugin and Pages](#13-djust-admin-plugin-and-pages)
  - [14. Dashboard Widget](#14-dashboard-widget)
- [Part 6: Verification & Troubleshooting](#part-6-verification--troubleshooting)
  - [15. Verification](#15-verification)
  - [16. Common Pitfalls](#16-common-pitfalls)
  - [17. Recovering from Migration Wrong-Order](#17-recovering-from-migration-wrong-order)

---

## Part 1: Setup

### 1. Installation

```bash
# With uv
uv add "djust-auth[oauth]"

# With pip
pip install "djust-auth[oauth]"
```

---

### 2. INSTALLED_APPS (order matters)

```python
INSTALLED_APPS = [
    # django builtins...
    "django.contrib.sites",     # ← MUST come before allauth.socialaccount
    "djust_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.openid_connect",  # for OIDC
    # or: github, google, gitlab
]
```

**Why `django.contrib.sites` first:** `socialaccount.0001_initial` has a hard
`("sites", "0001_initial")` dependency in its migration file. If `sites` is not in
`INSTALLED_APPS` before `socialaccount` is first migrated, you get
`InconsistentMigrationHistory`. This cannot be fixed with `--fake` without manually
creating the `django_site` table.

**Note on ordering:** The relative order of `djust_auth` and `allauth` doesn't matter —
what is non-negotiable is `django.contrib.sites` appearing before `allauth.socialaccount`.

---

### 3. MIDDLEWARE (AccountMiddleware goes last)

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # ← LAST, after XFrameOptions
]
```

Placing `AccountMiddleware` in the middle causes subtle OAuth redirect loops.

---

### 4. Migration Checklist

**Do this in order — order matters:**

1. Add `django.contrib.sites` to `INSTALLED_APPS` *before* `allauth.socialaccount`
2. Run `python manage.py migrate` (creates `django_site`, `account_*`, `socialaccount_*`)
3. Verify the default Site object exists:
   ```bash
   python manage.py shell -c "
   from django.contrib.sites.models import Site
   Site.objects.update_or_create(pk=1, defaults={'domain': 'localhost:8000', 'name': 'My App'})
   "
   ```

---

## Part 2: Configuration

### 5. Core Auth Settings

```python
SITE_ID = 1   # Required — SocialApp.sites is a M2M to django_site

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
SOCIALACCOUNT_AUTO_SIGNUP = True   # auto-create user on first OAuth login
SOCIALACCOUNT_LOGIN_ON_GET = True  # skip "confirm login?" page

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
```

**Why `SITE_ID`:** `allauth.socialaccount.models.SocialApp` (which stores OAuth
client_id/secret) is linked to sites via M2M. Without `SITE_ID`, allauth cannot resolve
which credentials to use for any provider. OAuth buttons won't render; login fails
silently.

---

### 6. OIDC Provider Config

```python
_OIDC_ENABLED = os.environ.get("OIDC_ENABLED", "false").lower() in ("true", "1", "yes")
if _OIDC_ENABLED:
    SOCIALACCOUNT_PROVIDERS = {
        "openid_connect": {
            "APPS": [
                {
                    "provider_id": "oidc",
                    "name": os.environ.get("OIDC_PROVIDER_NAME", "OIDC"),
                    "client_id": os.environ.get("OIDC_CLIENT_ID", ""),
                    "secret": os.environ.get("OIDC_CLIENT_SECRET", ""),
                    "settings": {
                        "server_url": os.environ.get("OIDC_SERVER_URL", ""),
                        # e.g. http://localhost:8090/realms/master for Keycloak
                        # allauth auto-appends /.well-known/openid-configuration
                        "token_auth_method": "client_secret_basic",
                    },
                }
            ]
        }
    }
```

Callback URI to register with the OIDC provider: `http://<host>/accounts/oidc/login/callback/`

---

### 7. Standard OAuth2 Providers (GitHub / Google / GitLab)

```python
SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APP": {"client_id": "...", "secret": "..."},
        "SCOPE": ["user:email"],   # SCOPE at provider level, NOT inside APP
    },
    "google": {
        "APP": {"client_id": "...", "secret": "..."},
        "SCOPE": ["profile", "email"],
    },
    "gitlab": {
        "APP": {"client_id": "...", "secret": "..."},
        "SCOPE": ["read_user"],
    },
}
```

Callback URIs: `http://<host>/accounts/<provider>/login/callback/`

---

### 8. URL Routing

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("djust_auth.urls")),   # login / logout / signup
    path("accounts/", include("allauth.urls")),       # OAuth callbacks
]
```

- `djust_auth.urls` (namespaced `djust_auth`): `/accounts/login/`, `/accounts/logout/`, `/accounts/signup/`
- `allauth.urls`: `/accounts/socialaccount/login/`, `/accounts/<provider>/login/callback/`, etc.

**Why both at `accounts/`:** allauth's internal `reverse()` and redirect URI handling is
hardcoded to the `/accounts/` namespace. The two `include()` calls don't conflict — they
match different path segments.

**Do NOT namespace `allauth.urls`** (e.g., `include("allauth.urls", namespace="allauth")`)
— this breaks all internal redirects.

---

### 9. Environment Variables

```bash
OIDC_ENABLED=true
OIDC_PROVIDER_NAME=Keycloak
OIDC_SERVER_URL=http://localhost:8090/realms/master
OIDC_CLIENT_ID=my-app
OIDC_CLIENT_SECRET=<secret>
# Callback URI: http://localhost:8000/accounts/oidc/login/callback/
```

---

## Part 3: Templates

### 10. Template Backends

#### Single-backend projects (standard Django)

Add the context processor to your `DjangoTemplates` backend:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "djust_auth.social.social_auth_providers",  # ← injects oauth_providers
            ],
        },
    },
]
```

#### Dual-backend projects (djust Rust backend + Django backend)

djust projects using the Rust-powered template backend require two separate backends.
The `social_auth_providers` context processor belongs **only** in the Django backend —
the djust Rust backend cannot use Django context processors.

```python
TEMPLATES = [
    {   # djust Rust backend — LiveView templates only
        "BACKEND": "djust.template_backend.DjustTemplateBackend",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {"context_processors": [...]},  # NO social_auth_providers here
    },
    {   # Django backend — admin + auth templates
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "django_templates"],   # separate dir from LiveView templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "djust_auth.social.social_auth_providers",  # ← here only
            ],
        },
    },
]
```

Auth templates go in `django_templates/`, not `templates/`.

---

### 11. Templates: Provided vs. Must-Create

**Provided by djust-auth** (auto-discovered via `APP_DIRS=True`):
- `djust_auth/includes/oauth_buttons.html` — reusable button list (Tailwind classes)
- `djust_auth/admin/providers.html` — OAuth Providers admin page
- `djust_auth/admin/social_accounts.html` — Social Accounts admin page
- `djust_auth/admin/widgets/auth_summary.html` — dashboard widget

**You must create** in your templates dir under `djust_auth/`:
- `login.html`
- `signup.html`

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

`oauth_providers` items: `name` (provider id), `label` (display name), `icon` (SVG
markup wrapped in `mark_safe()` — render unescaped with `{{ provider.icon }}`),
`login_url`. Built-in icons for GitHub, Google, GitLab.

---

## Part 4: Protecting djust LiveViews

### 12. Auth Mixins

`djust_auth.mixins` provides two drop-in mixins for protecting LiveView classes.
Both intercept at `dispatch()`, before `mount()` runs, so no LiveView state is
initialized for unauthorized users.

#### LoginRequiredLiveViewMixin

Redirects anonymous users to the login page with `?next=<current-path>`.

```python
from djust_auth.mixins import LoginRequiredLiveViewMixin
from djust import LiveView

class MyProtectedView(LoginRequiredLiveViewMixin, LiveView):
    template_name = "myapp/protected.html"

    # Optional: override login URL (defaults to settings.LOGIN_URL)
    login_url = "/accounts/login/"

    def mount(self, request, **kwargs):
        ...
```

#### PermissionRequiredLiveViewMixin

Raises `PermissionDenied` (HTTP 403) if the user lacks the specified permission.

```python
from djust_auth.mixins import PermissionRequiredLiveViewMixin
from djust import LiveView

class AdminOnlyView(PermissionRequiredLiveViewMixin, LiveView):
    template_name = "myapp/admin_only.html"
    permission_required = "myapp.change_mymodel"

    def mount(self, request, **kwargs):
        ...
```

#### Combining both

```python
from djust_auth.mixins import LoginRequiredLiveViewMixin, PermissionRequiredLiveViewMixin
from djust import LiveView

class StrictView(LoginRequiredLiveViewMixin, PermissionRequiredLiveViewMixin, LiveView):
    template_name = "myapp/strict.html"
    permission_required = "myapp.change_mymodel"
```

**MRO note:** Put `LoginRequiredLiveViewMixin` before `PermissionRequiredLiveViewMixin`
so unauthenticated users get a login redirect rather than a 403.

---

## Part 5: Admin Integration

### 13. djust Admin Plugin and Pages

`djust_admin.py` registers an `AuthAdminPlugin` with the djust admin site automatically
when `djust_auth` is installed. No extra configuration is needed.

The plugin adds two pages under the **Authentication** nav section:

| Page | URL path | Description |
|------|----------|-------------|
| OAuth Providers | `/admin/auth/providers` | Configured providers with callback URLs, masked client IDs, scope validation, settings snippets, and per-provider usage stats |
| Social Accounts | `/admin/auth/accounts` | LiveView table of linked accounts — searchable, sortable, filterable by provider, paginated (25/page) |

**OAuth Providers page** shows for each provider:
- Callback URL to register with the provider (`http://<host>/accounts/<id>/login/callback/`)
- Masked client ID (first 8 chars + last 4), secret presence indicator
- Configured scopes vs. recommended scopes
- Warning if `SCOPE` is misplaced inside `APP` instead of at provider level
- Copy-paste settings snippet with env var references
- Link to the provider's developer console

**Social Accounts page** (only shown when `allauth.socialaccount` is installed):
- Debounced search (username, email, uid)
- Provider filter dropdown
- Clickable column headers for sort/reverse-sort
- Pagination (25/page)

The `SocialAccount` allauth model is also registered with `DjustModelAdmin` when
`allauth.socialaccount` is installed.

---

### 14. Dashboard Widget

`AuthSummaryWidget` appears on the djust admin dashboard automatically. It displays:

| Stat | Source |
|------|--------|
| Total users | `User.objects.count()` |
| New this week | `date_joined >= now - 7d` |
| Staff users | `is_staff=True` |
| Superusers | `is_superuser=True` |
| OAuth users | Distinct users with a `SocialAccount` |
| OAuth providers | Count from allauth provider registry |

Template: `djust_auth/admin/widgets/auth_summary.html` (provided).
Widget `size = "lg"`, `order = 5` (renders early on the dashboard).

---

## Part 6: Verification & Troubleshooting

### 15. Verification

```bash
# Server starts without errors
python manage.py runserver

curl -o /dev/null -w "%{http_code}" http://localhost:8000/accounts/login/   # → 200
curl -o /dev/null -w "%{http_code}" http://localhost:8000/accounts/signup/  # → 200

# With OIDC_ENABLED=true, login page HTML contains provider label
curl -s http://localhost:8000/accounts/login/ | grep "Continue with"
```

---

### 16. Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `InconsistentMigrationHistory` on first migrate | `allauth.socialaccount` before `django.contrib.sites` in `INSTALLED_APPS` | Move `django.contrib.sites` above `allauth.socialaccount` |
| OAuth buttons missing / login fails silently | `SITE_ID` not set, or `django_site` row for pk=1 missing | Set `SITE_ID = 1` and run the `update_or_create` shell command in §4 |
| OAuth redirect loop | `AccountMiddleware` not last in `MIDDLEWARE` | Move it after `XFrameOptionsMiddleware` |
| `NoReverseMatch` for allauth URLs | `allauth.urls` included with a namespace | Remove `namespace=` from the `include()` call |
| `SCOPE` silently ignored | `SCOPE` placed inside `APP` dict instead of at provider level | Move `SCOPE` up one level (see §7) |
| `oauth_providers` empty in templates | `social_auth_providers` context processor added to djust Rust backend | Context processor belongs only in the `DjangoTemplates` backend |

---

### 17. Recovering from Migration Wrong-Order

If `allauth.socialaccount` was migrated before `django.contrib.sites` was added,
the `django_site` table won't exist and Django will refuse to run any migrations.

```python
# Run in: python manage.py shell
from django.db import connection
with connection.cursor() as c:
    c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('sites', '0001_initial', NOW()) ON CONFLICT DO NOTHING")
    c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('sites', '0002_alter_domain_unique', NOW()) ON CONFLICT DO NOTHING")
    c.execute("CREATE TABLE IF NOT EXISTS django_site (id SERIAL PRIMARY KEY, domain VARCHAR(100) NOT NULL UNIQUE, name VARCHAR(50) NOT NULL)")
    c.execute("INSERT INTO django_site (id, domain, name) VALUES (1, 'localhost', 'localhost') ON CONFLICT DO NOTHING")
# Then: python manage.py migrate
```
