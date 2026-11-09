import os
import threading

from locust import HttpUser, between, task


user_counter = 0
user_counter_lock = threading.Lock()


class RegistrationUser(HttpUser):
    wait_time = between(0, 1)

    host = os.getenv("LOCUST_HOST", "http://localhost:8000")

    session_id = os.getenv("LOCUST_SESSION_ID")

    def on_start(self):
        global user_counter

        if not self.session_id:
            print(
                "LOCUST_SESSION_ID is not set. "
                "Registration requests will be skipped."
            )
            return

        with user_counter_lock:
            user_counter += 1
            user_number = user_counter

        response = self.client.post(
            "/auth/login",
            json={
                "email": f"loadtest{user_number}@example.com",
                "password": "StrongPassword123",
            },
        )

        if response.status_code != 200:
            return

        self.access_token = response.json()["access_token"]

        self.client.headers.update(
            {
                "Authorization": (
                    f"Bearer {self.access_token}"
                )
            }
        )

    @task
    def register_for_session(self):
        if not self.session_id:
            return

        if getattr(self, "registration_attempted", False):
            return

        self.registration_attempted = True

        self.client.post(
            f"/sessions/{self.session_id}/register"
        )