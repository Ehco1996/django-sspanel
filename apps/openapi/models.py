from uuid import uuid4

from django.db import models

from apps.mixin import BaseModel
from apps.sspanel.models import User


def _gen_uuid_str() -> str:
    return str(uuid4())


class UserOpenAPIKey(BaseModel):
    name = models.CharField(max_length=32, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    key = models.CharField(max_length=64, default=_gen_uuid_str, db_index=True)

    class Meta:
        verbose_name = "用户秘钥"
        verbose_name_plural = "用户秘钥"

    @classmethod
    def get_by_key(cls, key: str):
        return cls.objects.filter(key=key).first()
