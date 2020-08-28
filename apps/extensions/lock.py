from django.http import Http404
from redis.lock import Lock, LockError


class GlobalLock(Lock):
    def __init__(
        self,
        name,
        redis_client,
        timeout=None,
        sleep=0.1,
        blocking=True,
        blocking_timeout=None,
        thread_local=True,
    ):
        if blocking is True:
            blocking_timeout = blocking_timeout or 5
        super(GlobalLock, self).__init__(
            name=name,
            redis=redis_client,
            timeout=timeout or 60 * 10,
            sleep=sleep,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
            thread_local=thread_local,
        )

    def __enter__(self):
        if self.acquire():
            return self
        else:
            # TODO 全局补货异常的mw
            raise Exception(f"key: {self.name} still locking")

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            super(GlobalLock, self).release()
        except LockError:
            pass


class LockManager:
    def __init__(self, redis_client) -> None:
        self._redis_client = redis_client

    def order_lock(self, order_number):
        key = f"lock.order_lock.{order_number}"
        return GlobalLock(key, self._redis_client, blocking=False)
