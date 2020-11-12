from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.signals import post_delete, post_save
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class CSRFExemptMixin:
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CSRFExemptMixin, self).dispatch(*args, **kwargs)


class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class SequenceMixin(models.Model):
    """
    提供一个sequence(排序)字段表示该记录在所有记录中的顺序

    基本的思路: 找到这条记录在所有序列里的位置 后洗一遍所有所有数据
    """

    class Meta:
        abstract = True

    MOVE_FORWARD = "forward"
    MOVE_BACK = "back"

    sequence = models.IntegerField(default=1, db_index=True, help_text="处于序列中的第几位")

    @transaction.atomic()
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
                    if move_direction == self.MOVE_FORWARD:
                        target_idx = idx
                    else:
                        target_idx = idx + 1
                    instance_list.insert(target_idx, self)
                    break
        seq = 1
        for instance in instance_list:
            instance.sequence = seq
            seq += 1

        cls = type(self)
        cls.objects.bulk_update(instance_list, ["sequence"])

    def update_all_sequence(self):
        # NOTE model 发生变动的时候自动更新整个序列
        cls = type(self)
        instance_list = list(cls.objects.all().order_by("sequence"))
        seq = 1
        for instance in instance_list:
            instance.sequence = seq
            seq += 1
        cls = type(self)
        cls.objects.bulk_update(instance_list, ["sequence"])


def _touch_sequence_model(sender, instance, **kw):
    if issubclass(sender, SequenceMixin):
        created = kw.get("created")
        if created is True or created is None:
            # NOTE from pose_save and post_delete
            instance.update_all_sequence()


post_save.connect(_touch_sequence_model)
post_delete.connect(_touch_sequence_model)
