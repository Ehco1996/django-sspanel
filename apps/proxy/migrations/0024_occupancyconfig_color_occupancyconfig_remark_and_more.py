# Generated by Django 4.2.6 on 2023-12-22 06:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proxy", "0023_alter_userproxynodeoccupancy_index_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="occupancyconfig",
            name="color",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "empty"),
                    ("is-info", "is-info"),
                    ("is-link", "is-link"),
                    ("is-primary", "is-primary"),
                    ("is-danger", "is-danger"),
                    ("is-warning", "is-warning"),
                    ("is-uccess", "is-success"),
                ],
                default="",
                max_length=32,
                verbose_name="颜色",
            ),
        ),
        migrations.AddField(
            model_name="occupancyconfig",
            name="remark",
            field=models.CharField(
                blank=True, default="", max_length=64, verbose_name="备注"
            ),
        ),
        migrations.AddField(
            model_name="occupancyconfig",
            name="status",
            field=models.CharField(
                choices=[("active", "active"), ("normal", "normal")],
                default="normal",
                max_length=32,
                verbose_name="状态",
            ),
        ),
    ]
