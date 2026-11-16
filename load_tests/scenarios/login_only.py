import os

from locust import HttpUser, task, between


class LoginOnlyUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self._login()

    @task
    def login(self):
        self._login()

    def _login(self):
        response = self.client.post(
            "/auth/login",
            json={
                "email": os.getenv(
                    "LOAD_TEST_EMAIL",
                    "loadtest1@example.com",
                ),
                "password": os.getenv(
                    "LOAD_TEST_PASSWORD",
                    "",
                ),
            },
        )

        if response.status_code != 200:
            response.raise_for_status()