from django.test import TestCase

from djust_auth.forms import SignupForm


class SignupFormTest(TestCase):
    def test_valid_form(self):
        form = SignupForm(
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            }
        )
        self.assertTrue(form.is_valid())

    def test_email_required(self):
        form = SignupForm(
            data={
                "username": "testuser",
                "email": "",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_passwords_must_match(self):
        form = SignupForm(
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password1": "SecurePass123!",
                "password2": "DifferentPass456!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
