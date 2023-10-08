# Generated by Django 3.1.2 on 2020-11-10 14:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sspanel", "0004_auto_20201108_0400"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="trojannode",
            name="certificateFile",
        ),
        migrations.RemoveField(
            model_name="trojannode",
            name="keyFile",
        ),
        migrations.AddField(
            model_name="trojannode",
            name="certificate_file",
            field=models.CharField(
                default="path/to/cert", max_length=64, verbose_name="crt地址"
            ),
        ),
        migrations.AddField(
            model_name="trojannode",
            name="key_file",
            field=models.CharField(
                default="path/to/cert", max_length=64, verbose_name="key地址"
            ),
        ),
        migrations.AddField(
            model_name="trojannode",
            name="skip_cert_verify",
            field=models.BooleanField(default=False, verbose_name="是否允许不安全连接(跳过tls验证)"),
        ),
        migrations.AlterField(
            model_name="ssnode",
            name="server",
            field=models.CharField(
                help_text="支持逗号分隔传多个地址", max_length=128, verbose_name="服务器地址"
            ),
        ),
        migrations.AlterField(
            model_name="trojannode",
            name="alpn",
            field=models.CharField(
                default="http/1.1", max_length=64, verbose_name="alpn"
            ),
        ),
        migrations.AlterField(
            model_name="trojannode",
            name="security",
            field=models.CharField(default="tls", max_length=64, verbose_name="加密方式"),
        ),
    ]
