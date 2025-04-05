from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class Category(models.Model):
    """
    Categories for tickets to organize them by department or topic.
    """
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,  # Change from CASCADE to SET_NULL
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('Parent category')
    )
    icon = models.CharField(_('Icon class'), max_length=50, blank=True)
    color = models.CharField(_('Color'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_all_children(self):
        """Get all child categories recursively"""
        children = list(self.subcategories.all())
        for child in self.subcategories.all():
            children.extend(child.get_all_children())
        return children

class Ticket(models.Model):
    """
    Main ticket model for support requests.
    """
    class Status(models.TextChoices):
        NEW = 'new', _('New')
        OPEN = 'open', _('Open')
        IN_PROGRESS = 'in_progress', _('In Progress')
        WAITING = 'waiting', _('Waiting on Customer')
        RESOLVED = 'resolved', _('Resolved')
        CLOSED = 'closed', _('Closed')

    class Branch(models.TextChoices):
        SIEGE = 'siege', _('Headquarters')
        YAOUNDE = 'yaounde', _('Yaoundé')
        DOUALA = 'douala', _('Douala')
        BUEA = 'buea', _('Buea')
        BAMENDA = 'bamenda', _('Bamenda')
        NGAOUNDERE = 'ngaoundere', _('Ngaoundere')
        GAROUA = 'garoua', _('Garoua')
        MAROUA = 'maroua', _('Maroua')
        BAFOUSSAM = 'bafoussam', _('Bafoussam')
        EBOLOWA = 'ebolowa', _('Ebolowa')
        BERTOUA = 'bertoua', _('Bertoua')

    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # Basic Fields
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'))
    office_door_number = models.CharField(_('Office Door Number'), max_length=20, blank=True, null=True, help_text=_('Optional: Enter the office door number for on-site visits'))
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True
    )
    branch = models.CharField(
        _('Branch'),
        max_length=64,
        choices=Branch.choices,
        default=Branch.SIEGE,
        db_index=True
    )
    priority = models.CharField(
        _('Priority'),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True
    )
    
    # Relationships
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tickets',
        verbose_name=_('Created by')
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        verbose_name=_('Assigned to'),
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='tickets',
        verbose_name=_('Category'),
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    due_date = models.DateTimeField(_('Due date'), null=True, blank=True)
    resolved_at = models.DateTimeField(_('Resolved at'), null=True, blank=True)
    closed_at = models.DateTimeField(_('Closed at'), null=True, blank=True)
    
    # Additional Fields
    tags = models.ManyToManyField('Tag', blank=True, related_name='tickets')
    sla_breach = models.BooleanField(_('SLA Breach'), default=False)
    is_public = models.BooleanField(_('Public ticket'), default=False)
    
    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-created_at']
        permissions = [
            ('assign_ticket', _('Can assign ticket to agent')),
            ('change_ticket_status', _('Can change ticket status')),
            ('view_all_tickets', _('Can view all tickets')),
        ]
        indexes = [
            models.Index(fields=['status', 'branch', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['due_date']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('ticket-detail', kwargs={'pk': self.pk})
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.due_date and timezone.now() > self.due_date:
            return True
        return False


class TicketAttachment(models.Model):
    """
    Files attached to tickets.
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Ticket')
    )
    file = models.FileField(_('File'), upload_to='ticket_attachments/%Y/%m/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_attachments',
        verbose_name=_('Uploaded by')
    )
    uploaded_at = models.DateTimeField(_('Uploaded at'), auto_now_add=True)
    description = models.CharField(_('Description'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('Ticket Attachment')
        verbose_name_plural = _('Ticket Attachments')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.ticket.title} - {self.file.name}"


class TicketHistory(models.Model):
    """
    History of changes to a ticket.
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name=_('Ticket')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ticket_changes',
        verbose_name=_('User')
    )
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    field_changed = models.CharField(_('Field changed'), max_length=100)
    old_value = models.TextField(_('Old value'), blank=True)
    new_value = models.TextField(_('New value'), blank=True)
    
    class Meta:
        verbose_name = _('Ticket History')
        verbose_name_plural = _('Ticket History')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.ticket.title} - {self.field_changed} changed by {self.user}"


class Tag(models.Model):
    """
    Tags for tickets to facilitate searching and categorization.
    """
    name = models.CharField(_('Name'), max_length=50, unique=True)
    color = models.CharField(_('Color'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SLA(models.Model):
    """
    Service Level Agreement settings.
    """
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    
    # Response time by priority
    response_time_low = models.PositiveIntegerField(_('Response time for low priority (hours)'), default=24)
    response_time_medium = models.PositiveIntegerField(_('Response time for medium priority (hours)'), default=12)
    response_time_high = models.PositiveIntegerField(_('Response time for high priority (hours)'), default=4)
    response_time_critical = models.PositiveIntegerField(_('Response time for critical priority (hours)'), default=1)
    
    # Resolution time by priority
    resolution_time_low = models.PositiveIntegerField(_('Resolution time for low priority (hours)'), default=72)
    resolution_time_medium = models.PositiveIntegerField(_('Resolution time for medium priority (hours)'), default=48)
    resolution_time_high = models.PositiveIntegerField(_('Resolution time for high priority (hours)'), default=24)
    resolution_time_critical = models.PositiveIntegerField(_('Resolution time for critical priority (hours)'), default=8)
    
    # Operating hours
    business_hours_only = models.BooleanField(_('Business hours only'), default=True)
    
    class Meta:
        verbose_name = _('SLA')
        verbose_name_plural = _('SLAs')
    
    def __str__(self):
        return self.name
    
    def get_response_time(self, priority):
        if priority == Ticket.Priority.LOW:
            return self.response_time_low
        elif priority == Ticket.Priority.MEDIUM:
            return self.response_time_medium
        elif priority == Ticket.Priority.HIGH:
            return self.response_time_high
        elif priority == Ticket.Priority.CRITICAL:
            return self.response_time_critical
        return 24  # Default
    
    def get_resolution_time(self, priority):
        if priority == Ticket.Priority.LOW:
            return self.resolution_time_low
        elif priority == Ticket.Priority.MEDIUM:
            return self.resolution_time_medium
        elif priority == Ticket.Priority.HIGH:
            return self.resolution_time_high
        elif priority == Ticket.Priority.CRITICAL:
            return self.resolution_time_critical
        return 72  # Default