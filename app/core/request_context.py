import contextvars
import uuid

request_id_context: contextvars.ContextVar[str | None] = (
    contextvars.ContextVar("request_id", default=None)
)

endpoint_context: contextvars.ContextVar[str | None] = (
    contextvars.ContextVar("endpoint", default=None)
)


def set_request_context(
    request_id: str,
    endpoint: str,
) -> tuple[contextvars.Token, contextvars.Token]:
    request_id_token = request_id_context.set(request_id)
    endpoint_token = endpoint_context.set(endpoint)

    return request_id_token, endpoint_token


def reset_request_context(
    request_id_token: contextvars.Token,
    endpoint_token: contextvars.Token,
) -> None:
    request_id_context.reset(request_id_token)
    endpoint_context.reset(endpoint_token)


def create_request_id() -> str:
    return str(uuid.uuid4())