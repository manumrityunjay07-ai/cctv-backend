import os
import logging
import redis  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Default to localhost if REDIS_HOST not in env
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

redis_client = None

def init_redis():
    global redis_client
    try:
        logger.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}")
        # Add a timeout to prevent hanging forever if Redis is unavailable
        redis_client = redis.Redis(  # type: ignore[attr-defined]
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            socket_timeout=2.0,
            decode_responses=True
        )
        # Test the connection
        redis_client.ping()
        logger.info("Successfully connected to Redis!")
        return True
    except redis.ConnectionError as e:  # type: ignore[attr-defined]
        logger.error(f"Redis connection error: {e}")
        redis_client = None
        return False
    except redis.TimeoutError as e:  # type: ignore[attr-defined]
        logger.error(f"Redis connection timeout: {e}")
        redis_client = None
        return False
    except Exception as e:
        logger.exception(f"Unexpected Redis error: {e}")
        redis_client = None
        return False

def get_redis_client():
    return redis_client

