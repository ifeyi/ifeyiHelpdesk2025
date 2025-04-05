from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import Ticket, TicketHistory
from accounts.models import User
from comments.models import Comment
from core.models import EmailLog, EmailSetting


def get_email_settings():
    """
    Get the email settings, creating default settings if they don't exist
    """
    settings, created = EmailSetting.objects.get_or_create(
        name="Default",
        defaults={
            "description": "Default email notification settings",
            "is_enabled": True,
            "notify_all_agents_on_new_ticket": True,
            "notify_customer_on_ticket_created": True,
            "notify_customer_on_status_change": True,
            "notify_customer_on_comment": True,
            "notify_agent_on_assignment": True,
            "notify_agent_on_comment": True,
        }
    )
    return settings

def send_notification_email(subject, template_name, context, recipient_list, email_type, related_object_id=None, related_object_type=None):
    """
    Send an HTML email notification with plain text alternative
    """
    # Check if notifications are enabled globally
    email_settings = get_email_settings()
    if not email_settings.is_enabled:
        return
    
    # Check specific notification type settings
    if email_type == 'ticket_created' and recipient_list[0].endswith('@creditfoncier.cm'):
        # This is going to an agent
        if not email_settings.notify_all_agents_on_new_ticket:
            return
        if email_settings.notify_selected_agents_only:
            # Filter recipients to only include selected agents
            selected_agent_emails = list(email_settings.selected_agents.values_list('email', flat=True))
            recipient_list = [email for email in recipient_list if email in selected_agent_emails]
            if not recipient_list:
                return
    elif email_type == 'ticket_created':
        # This is going to a customer
        if not email_settings.notify_customer_on_ticket_created:
            return
    elif email_type == 'ticket_assigned':
        if not email_settings.notify_agent_on_assignment:
            return
    elif email_type == 'status_change':
        if not email_settings.notify_customer_on_status_change:
            return
    elif email_type == 'comment_added' and not recipient_list[0].endswith('@creditfoncier.cm'):
        # This is going to a customer
        if not email_settings.notify_customer_on_comment:
            return
    elif email_type == 'comment_added' or email_type == 'internal_comment':
        # This is going to an agent
        if not email_settings.notify_agent_on_comment:
            return
    
    # Add email signature if configured
    if email_settings.email_signature:
        context['email_signature'] = email_settings.email_signature
        
    # Render HTML content
    html_content = render_to_string(f'emails/{template_name}.html', context)
    plain_text_content = render_to_string(f'emails/{template_name}.txt', context)
    
    # Log each email separately
    for recipient in recipient_list:
        email_log = EmailLog.objects.create(
            email_type=email_type,
            subject=subject,
            recipient=recipient,
            content=html_content,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            status=EmailLog.Status.PENDING
        )
        
        try:
            # Create the email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient]
            )
            
            # Attach HTML content
            msg.attach_alternative(html_content, "text/html")
            
            # Send the email
            msg.send()
            
            # Update the log
            email_log.status = EmailLog.Status.SENT
            email_log.sent_at = timezone.now()
            email_log.save()
            
        except Exception as e:
            # Log the error
            email_log.status = EmailLog.Status.FAILED
            email_log.error_message = str(e)
            email_log.save()


@receiver(post_save, sender=Ticket)
def ticket_notification(sender, instance, created, **kwargs):
    """
    Send email notifications when tickets are created or updated
    """
    # Get the site domain for use in URLs
    site_domain = settings.SITE_URL if hasattr(settings, 'SITE_URL') else "http://localhost:8000"
    
    # Prepare context data common to all emails
    context = {
        'ticket': instance,
        'ticket_url': f"{site_domain}{reverse('tickets:ticket-detail', kwargs={'pk': instance.pk})}",
    }
    
    if created:
        # Send notification to all agents for a new ticket
        agents = User.objects.filter(user_type=User.UserType.AGENT)
        agent_emails = [agent.email for agent in agents if agent.email]
        
        if agent_emails:
            send_notification_email(
                subject=f"[CFC Helpdesk] {_('New Ticket')}: {instance.title}",
                template_name='ticket_created_agent',
                context=context,
                recipient_list=agent_emails,
                email_type='ticket_created',
                related_object_id=instance.pk,
                related_object_type='ticket'
            )
        
        # Send confirmation to the ticket creator
        if instance.created_by and instance.created_by.email:
            send_notification_email(
                subject=f"[CFC Helpdesk] {_('Your ticket has been created')}: {instance.title}",
                template_name='ticket_created_customer',
                context=context,
                recipient_list=[instance.created_by.email],
                email_type='ticket_created',
                related_object_id=instance.pk,
                related_object_type='ticket'
            )
    else:
        # Get the latest history entry to determine what changed
        latest_change = TicketHistory.objects.filter(ticket=instance).order_by('-timestamp').first()
        
        if latest_change:
            context['change'] = latest_change
            
            # If the ticket is assigned to an agent, notify them
            if instance.assigned_to and instance.assigned_to.email and latest_change.field_changed == 'assigned_to':
                send_notification_email(
                    subject=f"[CFC Helpdesk] {_('Ticket Assigned to You')}: {instance.title}",
                    template_name='ticket_assigned',
                    context=context,
                    recipient_list=[instance.assigned_to.email],
                    email_type='ticket_assigned',
                    related_object_id=instance.pk,
                    related_object_type='ticket'
                )
            
            # Notify the customer of status changes
            if instance.created_by and instance.created_by.email and latest_change.field_changed == 'status':
                send_notification_email(
                    subject=f"[CFC Helpdesk] {_('Ticket Status Updated')}: {instance.title}",
                    template_name='ticket_status_update',
                    context=context, 
                    recipient_list=[instance.created_by.email],
                    email_type='status_change',
                    related_object_id=instance.pk,
                    related_object_type='ticket'
                )


@receiver(post_save, sender=Comment)
def comment_notification(sender, instance, created, **kwargs):
    """
    Send email notifications when comments are added to tickets
    """
    # Only process newly created comments
    if not created:
        return
        
    # Only send notifications for comments on tickets
    ticket_type = ContentType.objects.get_for_model(Ticket)
    if instance.content_type != ticket_type:
        return
    
    # Get the ticket for this comment
    try:
        ticket = Ticket.objects.get(pk=instance.object_id)
    except Ticket.DoesNotExist:
        return
    
    # Get the site domain for use in URLs
    site_domain = settings.SITE_URL if hasattr(settings, 'SITE_URL') else "http://localhost:8000"
    
    # Prepare context data
    context = {
        'ticket': ticket,
        'comment': instance,
        'author': instance.author,
        'ticket_url': f"{site_domain}{reverse('tickets:ticket-detail', kwargs={'pk': ticket.pk})}",
    }
    
    # Internal comments should only notify staff
    if instance.is_internal:
        # If the ticket is assigned, notify the assigned agent (if they're not the comment author)
        if ticket.assigned_to and ticket.assigned_to.email and ticket.assigned_to != instance.author:
            send_notification_email(
                subject=f"[CFC Helpdesk] {_('Internal Comment Added')}: {ticket.title}",
                template_name='internal_comment_added',
                context=context,
                recipient_list=[ticket.assigned_to.email],
                email_type='internal_comment',
                related_object_id=instance.pk,
                related_object_type='comment'
            )
    else:
        # Public comments should notify both the customer and the assigned agent
        recipients = []
        
        # Add customer email (if they're not the comment author)
        if ticket.created_by and ticket.created_by.email and ticket.created_by != instance.author:
            # Send notification to customer
            send_notification_email(
                subject=f"[CFC Helpdesk] {_('New Comment on Ticket')}: {ticket.title}",
                template_name='comment_added',
                context=context,
                recipient_list=[ticket.created_by.email],
                email_type='comment_added',
                related_object_id=instance.pk,
                related_object_type='comment'
            )
            
        # Add assigned agent email (if there is one and they're not the comment author)
        if ticket.assigned_to and ticket.assigned_to.email and ticket.assigned_to != instance.author:
            # Send notification to agent
            send_notification_email(
                subject=f"[CFC Helpdesk] {_('New Comment on Ticket')}: {ticket.title}",
                template_name='comment_added',
                context=context,
                recipient_list=[ticket.assigned_to.email],
                email_type='comment_added',
                related_object_id=instance.pk,
                related_object_type='comment'
            )