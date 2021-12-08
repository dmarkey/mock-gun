# Generated by Django 4.0 on 2021-12-08 17:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailAddress',
            fields=[
                ('address', models.CharField(max_length=1024, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='MockGunDomain',
            fields=[
                ('internal_id', models.CharField(editable=False, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_disabled', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=512, primary_key=True, serialize=False)),
                ('require_tls', models.BooleanField(default=False)),
                ('skip_verification', models.BooleanField(default=True)),
                ('type', models.CharField(default='sandbox', max_length=512)),
                ('smtp_login', models.CharField(default='postmaster@samples.mockgun.org', max_length=512)),
                ('web_prefix', models.CharField(default='email', max_length=512)),
                ('web_scheme', models.CharField(default='http', max_length=10)),
                ('wildcard', models.BooleanField(default=False)),
                ('state', models.CharField(choices=[('active', 'active'), ('unverified', 'unverified'), ('disabled', 'disabled')], default='active', max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('template', models.TextField()),
                ('name', models.CharField(max_length=256, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=256)),
                ('version', models.CharField(default='v1.0', max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='WebhookType',
            fields=[
                ('name', models.CharField(max_length=128, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='WebhookTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.mockgundomain')),
                ('webhook_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.webhooktype')),
            ],
        ),
        migrations.CreateModel(
            name='MockGunMessage',
            fields=[
                ('subject', models.CharField(max_length=512)),
                ('text', models.TextField(blank=True, default='')),
                ('html', models.TextField(blank=True, default='')),
                ('tag', models.CharField(blank=True, max_length=512)),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('raw_payload', models.JSONField()),
                ('bcc', models.ManyToManyField(blank=True, related_name='bcc', to='main_app.EmailAddress')),
                ('cc', models.ManyToManyField(blank=True, related_name='cc', to='main_app.EmailAddress')),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.mockgundomain')),
                ('from_field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_field', to='main_app.emailaddress')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.template')),
                ('to', models.ManyToManyField(related_name='to', to='main_app.EmailAddress')),
            ],
        ),
    ]
