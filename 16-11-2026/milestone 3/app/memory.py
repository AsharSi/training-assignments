"""Redis-backed per-session memory: recent messages + small structured context (active trip)."""
import json

import redis

from .config import REDIS_URL, SESSION_MAX_MESSAGES, SESSION_TTL_SECONDS

_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def ping() -> bool:
    try:
        return bool(_client.ping())
    except redis.RedisError:
        return False


def _hist_key(sid: str) -> str:
    return f"travel:session:{sid}:history"


def _ctx_key(sid: str) -> str:
    return f"travel:session:{sid}:context"


def add_message(sid: str, role: str, content: str) -> None:
    key = _hist_key(sid)
    pipe = _client.pipeline()
    pipe.rpush(key, json.dumps({"role": role, "content": content}))
    pipe.ltrim(key, -SESSION_MAX_MESSAGES, -1)
    pipe.expire(key, SESSION_TTL_SECONDS)
    pipe.execute()


def get_history(sid: str) -> list[dict]:
    return [json.loads(m) for m in _client.lrange(_hist_key(sid), 0, -1)]


def set_context(sid: str, **fields) -> None:
    key = _ctx_key(sid)
    clean = {k: str(v) for k, v in fields.items() if v is not None}
    if clean:
        _client.hset(key, mapping=clean)
        _client.expire(key, SESSION_TTL_SECONDS)


def get_context(sid: str) -> dict:
    return _client.hgetall(_ctx_key(sid))


def clear(sid: str) -> None:
    _client.delete(_hist_key(sid), _ctx_key(sid))
