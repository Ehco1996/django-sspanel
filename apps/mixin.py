from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.db import connection, models, transaction
from django.db.models.signals import post_delete, post_save, pre_save


class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class BaseModel(models.Model):
    """
    增加一些常用方法
    """

    class Meta:
        abstract = True

    @classmethod
    def get_or_none(cls, pk):
        return cls.objects.filter(pk=pk).first()

    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE {}".format(cls._meta.db_table))


class BaseLogModel(BaseModel):
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, help_text="创建时间", verbose_name="创建时间"
    )

    class Meta:
        abstract = True


class SequenceMixin(models.Model):
    """
    提供一个sequence(排序)字段表示该记录在所有记录中的顺序

    基本的思路: 找到这条记录在所有序列里的位置 后洗一遍所有所有数据
    """

    class Meta:
        abstract = True

    MOVE_FORWARD = "forward"
    MOVE_BACK = "back"

    sequence = models.IntegerField(
        "顺序", default=1, db_index=True, help_text="处于序列中的第几位"
    )

    @transaction.atomic
    def change_sequence(self, new_sequence, all_query):
        if new_sequence < 1:
            raise ValidationError(f"invalid sequence: {new_sequence}")

        # NOTE 该元素在数组里的移动方向
        move_direction = (
            self.MOVE_FORWARD if new_sequence <= self.sequence else self.MOVE_BACK
        )

        if not all_query:
            all_query = self._business_group_all_query()

        instance_list = list(all_query.exclude(pk=self.pk).order_by("sequence"))

        current_sequence = all_query.count()
        if new_sequence >= current_sequence:
            instance_list.append(self)
        else:
            for idx, instance in enumerate(instance_list):
                if instance.sequence >= new_sequence:
                    target_idx = idx if move_direction == self.MOVE_FORWARD else idx + 1
                    instance_list.insert(target_idx, self)
                    break
        for seq, instance in enumerate(instance_list, start=1):
            instance.sequence = seq
        cls = type(self)
        cls.objects.bulk_update(instance_list, ["sequence"])

    def update_all_sequence(self):
        cls = type(self)
        instance_list = list(cls.objects.all().order_by("sequence"))
        for seq, instance in enumerate(instance_list, start=1):
            instance.sequence = seq
        cls = type(self)
        cls.objects.bulk_update(instance_list, ["sequence"])


def _set_pre_save_sequence(sender, instance, *args, **kwargs):
    if issubclass(sender, SequenceMixin):
        old = sender.get_or_none(instance.id)
        if old:
            instance._pre_sequence = old.sequence


def _touch_sequence_model(sender, instance, **kw):
    # NOTE model sequence字段发生变动的时候自动更新整个序列
    if issubclass(sender, SequenceMixin):
        created = kw.get("created")
        if (
            created is True
            or created is None
            or (
                hasattr(instance, "_pre_sequence")
                and instance._pre_sequence != instance.sequence
            )
        ):
            # NOTE from pose_save and post_delete
            if (
                hasattr(instance, "_pre_sequence")
                and instance._pre_sequence != instance.sequence
            ):
                cls = type(instance)
                instance.change_sequence(
                    instance.sequence, cls.objects.all().order_by("sequence")
                )
            else:
                instance.update_all_sequence()


pre_save.connect(_set_pre_save_sequence)
post_save.connect(_touch_sequence_model)
post_delete.connect(_touch_sequence_model)
