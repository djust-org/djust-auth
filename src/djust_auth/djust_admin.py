"""djust-admin plugin for djust-auth.

Registers an Authentication plugin with:
- Dashboard widget showing user/auth stats
- OAuth Providers admin page
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from djust_admin import site
from djust_admin.plugins import AdminPage, AdminPlugin, AdminWidget

from .admin_views import OAuthProvidersView


class AuthSummaryWidget(AdminWidget):
    """Dashboard widget showing user and auth statistics."""

    widget_id = "auth_summary"
    label = "Authentication"
    template_name = "djust_auth/admin/widgets/auth_summary.html"
    order = 5
    size = "md"

    def get_context(self, request):
        User = get_user_model()
        week_ago = timezone.now() - timedelta(days=7)

        # Count configured OAuth providers
        oauth_count = 0
        try:
            from django.apps import apps

            if apps.is_installed("allauth.socialaccount"):
                from allauth.socialaccount.providers import registry

                if not registry.loaded:
                    registry.load()
                oauth_count = len(registry.get_class_list())
        except Exception:
            pass

        return {
            "total_users": User.objects.count(),
            "recent_signups": User.objects.filter(date_joined__gte=week_ago).count(),
            "staff_users": User.objects.filter(is_staff=True).count(),
            "oauth_providers": oauth_count,
        }


class AuthAdminPlugin(AdminPlugin):
    name = "auth"
    verbose_name = "Authentication"

    def get_pages(self):
        return [
            AdminPage(
                url_path="auth/providers",
                url_name="auth_providers",
                view_class=OAuthProvidersView,
                label="OAuth Providers",
                icon="🔑",
                nav_section="Authentication",
                nav_order=10,
            ),
        ]

    def get_widgets(self):
        return [AuthSummaryWidget()]


site.register_plugin(AuthAdminPlugin)
