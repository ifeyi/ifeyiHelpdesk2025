import logging
from django.conf import settings
from django.dispatch import receiver
from django_auth_ldap.backend import populate_user, LDAPBackend
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from .models import User, AgentProfile, CustomerProfile

logger = logging.getLogger('accounts.signals')

@receiver(populate_user)
def set_user_type_from_groups(sender, user=None, ldap_user=None, **kwargs):
    """
    Signal handler that sets the user type and creates appropriate profiles based on
    the Active Directory groups the user belongs to.
    
    This version preserves manually set user types for existing users.
    """
    if not user or not ldap_user:
        return

    logger.debug(f"Processing LDAP user: {user.username}")
    
    # Check if this is a new user (no ID yet) or has never been configured
    is_new_user = user.pk is None

    # Only update user_type if it's a new user or we've never manually set it
    # If the user already exists in DB and has a non-default user_type, preserve it
    if is_new_user:
        logger.debug(f"New user {user.username}, setting up user type based on AD groups")
        # Get group DNs for this user
        user_groups = []
        if hasattr(ldap_user, 'group_dns'):
            user_groups = ldap_user.group_dns
            logger.debug(f"User groups: {user_groups}")
        
        # Get the group mapping from settings
        group_mapping = getattr(settings, 'AUTH_LDAP_GROUP_MAPPING', {})
        
        # Determine user type based on group membership
        assigned_user_type = None
        
        # Check each user type and its corresponding AD groups
        for user_type, group_dns in group_mapping.items():
            matching_groups = [grp for grp in group_dns if grp in user_groups]
            
            if matching_groups:
                logger.debug(f"User matches groups for {user_type}: {matching_groups}")
                assigned_user_type = user_type
                # Admin has highest priority
                if user_type == 'admin':
                    break
        
        # Set default type if no match found
        if assigned_user_type is None:
            assigned_user_type = 'customer'
            logger.debug(f"No group match found, defaulting to {assigned_user_type}")
        
        # Update user type
        user.user_type = assigned_user_type
    else:
        logger.debug(f"Existing user {user.username} with type {user.user_type} - preserving user type")
    
    # Always update these fields from LDAP for all users
    if hasattr(ldap_user, 'attrs'):
        # Update department if available
        if 'department' in ldap_user.attrs:
            try:
                user.department = ldap_user.attrs['department'][0].decode('utf-8')
            except (IndexError, AttributeError):
                pass
        
        # Update phone if available
        if 'telephoneNumber' in ldap_user.attrs:
            try:
                user.phone = ldap_user.attrs['telephoneNumber'][0].decode('utf-8')
            except (IndexError, AttributeError):
                pass
    
    # Save the user after modifications
    user.save()
    
    # Create appropriate profile based on user_type if it doesn't exist
    if user.user_type == User.UserType.AGENT and not hasattr(user, 'agent_profile'):
        try:
            AgentProfile.objects.get_or_create(user=user)
            logger.debug(f"Created agent profile for {user.username}")
        except Exception as e:
            logger.error(f"Error creating agent profile: {e}")
    
    elif user.user_type == User.UserType.CUSTOMER and not hasattr(user, 'customer_profile'):
        try:
            # For customers, try to extract company/account info from LDAP
            company = ""
            if hasattr(ldap_user, 'attrs') and 'company' in ldap_user.attrs:
                try:
                    company = ldap_user.attrs['company'][0].decode('utf-8')
                except (IndexError, AttributeError):
                    pass
                
            CustomerProfile.objects.get_or_create(
                user=user,
                defaults={'company': company}
            )
            logger.debug(f"Created customer profile for {user.username}")
        except Exception as e:
            logger.error(f"Error creating customer profile: {e}")


@receiver(user_logged_in)
def send_first_login_email(sender, request, user, **kwargs):
    """
    Send a welcome email to users on their first login.
    We use the user_logged_in signal to detect successful logins.
    """
    try:
        # Check if this is the user's first login by looking at the last_login field
        # Note: The last_login is updated after this signal, so if previous_last_login is None,
        # this is the first login
        previous_login = User.objects.filter(pk=user.pk).values_list('last_login', flat=True).first()
        
        if previous_login is None:
            logger.info(f"First login detected for user: {user.username}")
            
            # Prepare email content
            subject = _('Welcome to CFC Helpdesk System')
            
            # Render HTML email from template
            html_message = render_to_string('accounts/emails/welcome_email.html', {
                'user': user,
                'helpdesk_url': request.build_absolute_uri('/'),
                'user_type': user.get_user_type_display()
            })
            
            # Plain text version as backup
            plain_message = _(f"""
Hello {user.get_full_name() or user.username},

Welcome to the CFC Helpdesk System! Your account has been successfully created and you are now logged in.

Your account type is: {user.get_user_type_display()}

You can access the helpdesk system at: {request.build_absolute_uri('/')}

If you have any questions, please contact the IT department.

Thank you,
CFC Helpdesk Team
""")
            
            # Send the email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent to {user.email}")
            
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")