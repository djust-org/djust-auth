from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.views import View

from djust_auth.mixins import LoginRequiredLiveViewMixin, PermissionRequiredLiveViewMixin


class StubView(LoginRequiredLiveViewMixin, View):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if isinstance(response, HttpResponse) and response.status_code == 302:
            return response
        return HttpResponse("OK")


class StubPermView(PermissionRequiredLiveViewMixin, View):
    permission_required = "auth.view_user"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if isinstance(response, HttpResponse) and response.status_code in (302, 403):
            return response
        return HttpResponse("OK")


class LoginRequiredMixinTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_anonymous_user_redirected(self):
        request = self.factory.get("/protected/")
        request.user = AnonymousUser()
        response = StubView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_next_param_preserved(self):
        request = self.factory.get("/protected/page/")
        request.user = AnonymousUser()
        response = StubView.as_view()(request)
        self.assertIn("next=%2Fprotected%2Fpage%2F", response.url)

    def test_authenticated_user_passes(self):
        request = self.factory.get("/protected/")
        request.user = self.user
        response = StubView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_custom_login_url(self):
        request = self.factory.get("/protected/")
        request.user = AnonymousUser()
        response = StubView.as_view(login_url="/custom/login/")(request)
        self.assertIn("/custom/login/", response.url)


class PermissionRequiredMixinTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_user_without_perm_denied(self):
        request = self.factory.get("/protected/")
        request.user = self.user
        with self.assertRaises(Exception):
            StubPermView.as_view()(request)

    def test_user_with_perm_passes(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(User)
        perm = Permission.objects.get(codename="view_user", content_type=ct)
        self.user.user_permissions.add(perm)
        self.user = User.objects.get(pk=self.user.pk)  # Refresh cache

        request = self.factory.get("/protected/")
        request.user = self.user
        response = StubPermView.as_view()(request)
        self.assertEqual(response.status_code, 200)
