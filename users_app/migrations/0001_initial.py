# Generated by Django 5.1.1 on 2024-09-29 08:49

import dirtyfields.dirtyfields
import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
import users_app.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('username', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('bio', models.TextField(blank=True, null=True)),
                ('location', models.CharField(blank=True, choices=[('Tashkent', 'Tashkent')], max_length=50, null=True)),
                ('email', models.EmailField(blank=True, max_length=50, null=True, unique=True)),
                ('phone_number', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('banner_color', models.CharField(blank=True, default='#000000', max_length=7, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female')], max_length=6, null=True)),
                ('auth_type', models.CharField(choices=[('email', 'Email'), ('phone', 'Phone')], default='email', max_length=5)),
                ('telegram_username', models.CharField(blank=True, max_length=100, null=True)),
                ('instagram_username', models.CharField(blank=True, max_length=100, null=True)),
                ('twitter_username', models.CharField(blank=True, max_length=100, null=True)),
                ('youtube_channel', models.CharField(blank=True, max_length=100, null=True)),
                ('github_username', models.CharField(blank=True, max_length=100, null=True)),
                ('education', models.CharField(blank=True, max_length=50, null=True)),
                ('avatar', models.ImageField(default='defaults/default_avatar.png', upload_to=users_app.models.user_directory_path)),
                ('banner', models.ImageField(default='defaults/default_banner.png', upload_to=users_app.models.user_directory_path)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('profession', models.OneToOneField(blank=True, max_length=50, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='users_app.profession')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            bases=(models.Model, dirtyfields.dirtyfields.DirtyFieldsMixin),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Tab',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=20)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tabs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('body', models.TextField()),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='users_app.tab')),
            ],
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower', to=settings.AUTH_USER_MODEL)),
                ('following', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('follower', 'following'), name='follower_following_unique')],
            },
        ),
        migrations.AddConstraint(
            model_name='tab',
            constraint=models.UniqueConstraint(fields=('owner', 'name'), name='tab_owner_name_unique'),
        ),
        migrations.AddConstraint(
            model_name='note',
            constraint=models.UniqueConstraint(fields=('owner', 'body'), name='owner_body_unique'),
        ),
    ]
