# Generated by Django 4.2.6 on 2023-12-17 03:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("proxy", "0020_alter_proxynode_ehco_reload_interval"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usertrafficlog",
            name="proxy_node",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="proxy.proxynode",
                verbose_name="代理节点",
            ),
        ),
        migrations.AlterField(
            model_name="usertrafficlog",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="用户",
            ),
        ),
    ]
