"""LiveView pages for the djust-auth admin plugin."""

from django.contrib.auth import get_user_model
from djust import LiveView

from djust_admin.views import AdminBaseMixin


class OAuthProvidersView(AdminBaseMixin, LiveView):
    """Admin page showing configured OAuth providers and their status."""

    template_name = "djust_auth/admin/providers.html"

    def mount(self, request, **kwargs):
        self.request = request

    def get_context_data(self, **kwargs):
        providers = self._get_providers()
        User = get_user_model()

        return {
            **self.get_admin_context(),
            "title": "OAuth Providers",
            "providers": providers,
            "total_users": User.objects.count(),
            "allauth_installed": self._is_allauth_installed(),
        }

    def _is_allauth_installed(self):
        try:
            from django.apps import apps

            return apps.is_installed("allauth.socialaccount")
        except Exception:
            return False

    def _get_providers(self):
        """Build provider status list from allauth configuration."""
        if not self._is_allauth_installed():
            return []

        try:
            from allauth.socialaccount.providers import registry

            if not registry.loaded:
                registry.load()
        except Exception:
            return []

        from django.conf import settings

        configured_providers = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {})

        # Provider icons (reuse from social.py)
        icons = {
            "github": "GH",
            "google": "G",
            "gitlab": "GL",
            "microsoft": "MS",
            "twitter": "X",
            "facebook": "FB",
        }

        providers = []
        for provider_cls in registry.get_class_list():
            pid = provider_cls.id
            provider_conf = configured_providers.get(pid, {})
            app_conf = provider_conf.get("APP", {})
            has_credentials = bool(app_conf.get("client_id"))

            # Count social accounts for this provider
            social_account_count = 0
            try:
                from allauth.socialaccount.models import SocialAccount

                social_account_count = SocialAccount.objects.filter(
                    provider=pid
                ).count()
            except Exception:
                pass

            providers.append({
                "id": pid,
                "name": provider_cls.name,
                "icon": icons.get(pid, pid[:2].upper()),
                "has_credentials": has_credentials,
                "account_count": social_account_count,
            })

        return providers
