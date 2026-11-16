import logging
import time
from collections.abc import Generator
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

from app.core.request_context import (
    endpoint_context,
    request_id_context,
)

logger = logging.getLogger("app.db_pool")

engine = create_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_timeout=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

_connection_checkout_times = {}


@event.listens_for(engine, "checkout")
def record_checkout(
    dbapi_connection,
    connection_record,
    connection_proxy,
):
    _connection_checkout_times[id(dbapi_connection)] = (
        time.perf_counter()
    )

    request_id = request_id_context.get()
    endpoint = endpoint_context.get()

    print(
        f"REQUEST_ID={request_id} "
        f"ENDPOINT={endpoint} "
        f"PID={os.getpid()} "
        f"EVENT=CHECKOUT "
        f"DB_CONNECTIONS_CHECKED_OUT={engine.pool.checkedout()}",
        flush=True,
    )


@event.listens_for(engine, "checkin")
def record_checkin(
    dbapi_connection,
    connection_record,
):
    checkout_time = _connection_checkout_times.pop(
        id(dbapi_connection),
        None,
    )

    if checkout_time is not None:
        hold_time_ms = (
            time.perf_counter() - checkout_time
        ) * 1000

        request_id = request_id_context.get()
        endpoint = endpoint_context.get()
        checked_out_connections = engine.pool.checkedout()

        print(
            f"REQUEST_ID={request_id} "
            f"ENDPOINT={endpoint} "
            f"PID={os.getpid()} "
            f"DB_CONNECTION_HOLD_MS={hold_time_ms:.2f} "
            f"DB_CONNECTIONS_CHECKED_OUT={checked_out_connections}",
            flush=True,
        )

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
