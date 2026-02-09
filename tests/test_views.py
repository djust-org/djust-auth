from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings


@override_settings(
    ROOT_URLCONF="djust_auth.urls",
    LOGIN_REDIRECT_URL="/dashboard/",
    LOGOUT_REDIRECT_URL="/",
)
class SignupViewTest(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        client = Client()
        response = client.post(
            "/signup/",
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "new@example.com")

    def test_signup_redirects_to_login_redirect_url(self):
        client = Client()
        response = client.post(
            "/signup/",
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)


@override_settings(
    ROOT_URLCONF="djust_auth.urls",
    LOGOUT_REDIRECT_URL="/",
)
class LogoutViewTest(TestCase):
    def test_logout_clears_session(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        client = Client()
        client.login(username="testuser", password="testpass123")
        response = client.get("/logout/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/", fetch_redirect_response=False)
