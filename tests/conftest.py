import django
from django.conf import settings


def pytest_configure():
    settings.configure(
        SECRET_KEY="test-secret-key-for-djust-auth",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "djust_auth",
        ],
        ROOT_URLCONF="djust_auth.urls",
        LOGIN_URL="/accounts/login/",
        LOGIN_REDIRECT_URL="/dashboard/",
        LOGOUT_REDIRECT_URL="/",
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
        ],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )
    django.setup()
