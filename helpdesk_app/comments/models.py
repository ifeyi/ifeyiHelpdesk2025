from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class Comment(models.Model):
    """
    Generic comment model that can be attached to tickets, articles, etc.
    """
    # Generic foreign key to the commented object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Content type')
    )
    object_id = models.PositiveIntegerField(_('Object ID'))
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Comment details
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='comments',
        verbose_name=_('Author')
    )
    text = models.TextField(_('Text'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # Comment settings
    is_internal = models.BooleanField(
        _('Internal comment'),
        default=False,
        help_text=_('Internal comments are only visible to staff members')
    )
    is_edited = models.BooleanField(_('Edited'), default=False)
    
    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
        ]
        permissions = [
            ('view_internal_comments', _('Can view internal comments')),
        ]
    
    def __str__(self):
        return f"{self.author} on {self.content_object}"


class CommentAttachment(models.Model):
    """
    Files attached to comments.
    """
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Comment')
    )
    file = models.FileField(_('File'), upload_to='comment_attachments/%Y/%m/')
    uploaded_at = models.DateTimeField(_('Uploaded at'), auto_now_add=True)
    description = models.CharField(_('Description'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('Comment Attachment')
        verbose_name_plural = _('Comment Attachments')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Attachment for {self.comment}"