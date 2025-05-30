# Generated by Django 4.2.10 on 2025-04-29 14:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(verbose_name='Object ID')),
                ('text', models.TextField(verbose_name='Text')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('is_internal', models.BooleanField(default=False, help_text='Internal comments are only visible to staff members', verbose_name='Internal comment')),
                ('is_edited', models.BooleanField(default=False, verbose_name='Edited')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='comments', to=settings.AUTH_USER_MODEL, verbose_name='Author')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Content type')),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
                'ordering': ['created_at'],
                'permissions': [('view_internal_comments', 'Can view internal comments')],
            },
        ),
        migrations.CreateModel(
            name='CommentAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='comment_attachments/%Y/%m/', verbose_name='File')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Uploaded at')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='Description')),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='comments.comment', verbose_name='Comment')),
            ],
            options={
                'verbose_name': 'Comment Attachment',
                'verbose_name_plural': 'Comment Attachments',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['content_type', 'object_id'], name='comments_co_content_cff8bd_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['created_at'], name='comments_co_created_5f6a12_idx'),
        ),
    ]
