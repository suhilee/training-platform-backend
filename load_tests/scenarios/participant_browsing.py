import os
import random

from locust import HttpUser, between, task


class TrainingPlatformParticipant(HttpUser):
    wait_time = between(1, 3)

    host = os.getenv("LOCUST_HOST", "http://localhost:8000")

    session_id = os.getenv("4ce87913-9e9d-4e87-8ed2-3df35fb38eb0")

    def on_start(self):
        user_number = random.randint(1, 100)

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

    @task(3)
    def list_eligible_sessions(self):
        self.client.get("/sessions")

    @task(2)
    def list_my_sessions(self):
        self.client.get("/sessions/my")

    @task(1)
    def get_session_detail(self):
        if not self.session_id:
            return

        self.client.get(
            f"/sessions/{self.session_id}"
        )

