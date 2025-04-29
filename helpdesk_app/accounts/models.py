from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class UserType(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        AGENT = 'agent', _('Agent')
        CUSTOMER = 'customer', _('Customer')
    
    email = models.EmailField(_('Email address'), unique=True)
    user_type = models.CharField(
        _('User type'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.CUSTOMER
    )
    department = models.CharField(_('Department'), max_length=100, blank=True)
    phone = models.CharField(_('Phone number'), max_length=20, blank=True)
    profile_picture = models.ImageField(
        _('Profile picture'),
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.email
    
    @property
    def is_admin(self):
        return self.user_type == self.UserType.ADMIN
    
    @property
    def is_agent(self):
        return self.user_type == self.UserType.AGENT
    
    @property
    def is_customer(self):
        return self.user_type == self.UserType.CUSTOMER


class AgentProfile(models.Model):
    """
    Extended profile for agents with additional details.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        primary_key=True
    )
    expertise = models.ManyToManyField('tickets.Category', blank=True, related_name='expert_agents')
    bio = models.TextField(_('Biography'), blank=True)
    availability_status = models.BooleanField(_('Available'), default=True)
    max_tickets = models.PositiveIntegerField(_('Maximum tickets'), default=20)

    class Meta:
        verbose_name = _('Agent Profile')
        verbose_name_plural = _('Agent Profiles')

    def __str__(self):
        return f"Agent: {self.user.email}"


class CustomerProfile(models.Model):
    """
    Extended profile for customers with additional details.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        primary_key=True
    )
    company = models.CharField(_('Company'), max_length=100, blank=True)
    account_id = models.CharField(_('Account ID'), max_length=100, blank=True)
    support_level = models.CharField(_('Support Level'), max_length=50, blank=True)
    
    class Meta:
        verbose_name = _('Customer Profile')
        verbose_name_plural = _('Customer Profiles')

    def __str__(self):
        return f"Customer: {self.user.email}"
    

def get_user_type_display(self):
    """
    Returns the display name of the user type.
    Used in welcome emails and other places.
    """
    return dict(self.UserType.choices).get(self.user_type, "Unknown")