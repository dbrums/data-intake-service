"""RQ queue initialization for background job processing."""

import logging

from redis import Redis, RedisError
from rq import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-initialized global queue
_queue: Queue | None = None
_redis_conn: Redis | None = None


def _init_redis() -> Redis:
    """Initialize Redis connection with error handling."""
    try:
        # Parse REDIS_URL from settings
        # Format: redis://[:password@]host:port/db
        redis_conn = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,  # RQ expects bytes
            socket_connect_timeout=5,
            socket_timeout=5,
        )

        # Test connection
        redis_conn.ping()
        logger.info(
            "Redis connection established: %s",
            settings.REDIS_URL.split("@")[-1],  # Don't log password
        )
        return redis_conn

    except RedisError as e:
        logger.error("Redis connection failed: %s", str(e))
        raise


def get_queue() -> Queue:
    """Get or initialize the RQ queue (lazy initialization).

    Uses lazy initialization to avoid Redis connection attempts during
    test collection/import. The queue is created on first access and
    reused for subsequent calls.

    Returns:
        Queue: The initialized RQ queue instance.

    Raises:
        RedisError: If Redis connection fails.
    """
    global _queue, _redis_conn

    if _queue is None:
        _redis_conn = _init_redis()
        _queue = Queue(
            name="default",
            connection=_redis_conn,
            default_timeout=600,
        )
        logger.info("RQ queue initialized: %s", _queue.name)

    return _queue
