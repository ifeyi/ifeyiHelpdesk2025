from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class EmailLog(models.Model):
    """
    Tracks all emails sent by the helpdesk system
    """
    class EmailType(models.TextChoices):
        TICKET_CREATED = 'ticket_created', _('Ticket Created')
        TICKET_ASSIGNED = 'ticket_assigned', _('Ticket Assigned')
        TICKET_UPDATED = 'ticket_updated', _('Ticket Updated')
        COMMENT_ADDED = 'comment_added', _('Comment Added')
        INTERNAL_COMMENT = 'internal_comment', _('Internal Comment')
        STATUS_CHANGE = 'status_change', _('Status Change')
        OTHER = 'other', _('Other')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SENT = 'sent', _('Sent')
        FAILED = 'failed', _('Failed')
        
    email_type = models.CharField(
        _('Email Type'),
        max_length=50,
        choices=EmailType.choices,
        default=EmailType.OTHER
    )
    subject = models.CharField(_('Subject'), max_length=255)
    recipient = models.EmailField(_('Recipient'))
    content = models.TextField(_('Content'), blank=True)
    related_object_id = models.PositiveIntegerField(_('Related Object ID'), null=True, blank=True)
    related_object_type = models.CharField(_('Related Object Type'), max_length=100, blank=True)
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    error_message = models.TextField(_('Error Message'), blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    sent_at = models.DateTimeField(_('Sent At'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Email Log')
        verbose_name_plural = _('Email Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['recipient']),
        ]
    
    def __str__(self):
        return f"{self.get_email_type_display()} to {self.recipient} ({self.get_status_display()})"


class EmailSetting(models.Model):
    """
    Configurable email notification settings
    """
    name = models.CharField(_('Setting Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)
    is_enabled = models.BooleanField(_('Enabled'), default=True)
    
    # Global settings
    email_signature = models.TextField(_('Email Signature'), blank=True, 
                                     help_text=_('Signature to append to all emails'))
    
    # Notification settings
    notify_all_agents_on_new_ticket = models.BooleanField(
        _('Notify all agents on new ticket'), 
        default=True
    )
    notify_selected_agents_only = models.BooleanField(
        _('Notify only selected agents'), 
        default=False,
        help_text=_('If enabled, only agents in selected_agents will be notified')
    )
    selected_agents = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True,
        related_name='notification_settings',
        verbose_name=_('Selected Agents'),
        limit_choices_to={'user_type': 'agent'}
    )
    
    # Customer notification settings
    notify_customer_on_ticket_created = models.BooleanField(
        _('Notify customer when ticket is created'),
        default=True
    )
    notify_customer_on_status_change = models.BooleanField(
        _('Notify customer on status change'),
        default=True
    )
    notify_customer_on_comment = models.BooleanField(
        _('Notify customer when comment is added'),
        default=True
    )
    
    # Agent notification settings
    notify_agent_on_assignment = models.BooleanField(
        _('Notify agent when ticket is assigned'),
        default=True
    )
    notify_agent_on_comment = models.BooleanField(
        _('Notify agent when comment is added'),
        default=True
    )
    
    class Meta:
        verbose_name = _('Email Setting')
        verbose_name_plural = _('Email Settings')
    
    def __str__(self):
        return self.name