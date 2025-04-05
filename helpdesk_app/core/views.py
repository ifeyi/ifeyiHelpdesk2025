from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from articles.models import Article
from django.db.models import Count, Avg, F, Q, ExpressionWrapper, DurationField, FloatField
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models.functions import ExtractHour
from datetime import timedelta, datetime
from django.http import HttpResponse
from .models import EmailLog, EmailSetting
from tickets.models import Ticket, TicketHistory
from accounts.models import User
from comments.models import Comment
from django.contrib.contenttypes.models import ContentType
import json
import random

class HomeView(TemplateView):
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Only add dashboard data for authenticated users
        if self.request.user.is_authenticated:
            user = self.request.user
            
            # Get user's tickets
            if user.is_staff or user.user_type == 'agent':
                # For staff and agents, show assigned and recent tickets
                context['assigned_tickets'] = Ticket.objects.filter(
                    assigned_to=user
                ).order_by('-created_at')[:5]
                
                # Get ticket statistics
                context['ticket_stats'] = {
                    'new': Ticket.objects.filter(status=Ticket.Status.NEW).count(),
                    'open': Ticket.objects.filter(status=Ticket.Status.OPEN).count(),
                    'in_progress': Ticket.objects.filter(status=Ticket.Status.IN_PROGRESS).count(),
                    'waiting': Ticket.objects.filter(status=Ticket.Status.WAITING).count(),
                    'resolved': Ticket.objects.filter(status=Ticket.Status.RESOLVED).count(),
                }
            else:
                # For customers, show their submitted tickets
                context['user_tickets'] = Ticket.objects.filter(
                    created_by=user
                ).order_by('-created_at')[:5]
            
            # Get recent articles for all users
            context['recent_articles'] = Article.objects.filter(
                status=Article.Status.PUBLISHED
            ).order_by('-published_at')[:5]
        
        return context

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Only provide full dashboard for staff/agents
        if not (user.is_staff or user.user_type == 'agent'):
            return self.get_customer_dashboard(context, user)
        
        # Time periods for filtering
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Open tickets query - reused in multiple places
        open_tickets = Ticket.objects.filter(
            Q(status=Ticket.Status.NEW) |
            Q(status=Ticket.Status.OPEN) |
            Q(status=Ticket.Status.IN_PROGRESS) |
            Q(status=Ticket.Status.WAITING)
        )
        
        context['open_tickets'] = open_tickets
        
        # Quick stat cards
        context['tickets_resolved_this_week'] = Ticket.objects.filter(
            status=Ticket.Status.RESOLVED,
            resolved_at__gte=week_ago
        ).count()
        
        # Calculate average response time
        # For this, we'll use first comment on tickets as a proxy for response time
        ticket_type = ContentType.objects.get_for_model(Ticket)
        
        # Get all tickets created in the last month
        recent_tickets = Ticket.objects.filter(created_at__gte=month_ago)
        
        total_response_time = 0
        response_count = 0
        
        for ticket in recent_tickets:
            # Get the earliest comment by staff/agent (not by the ticket creator)
            first_comment = Comment.objects.filter(
                content_type=ticket_type,
                object_id=ticket.id,
                author__isnull=False
            ).exclude(
                author=ticket.created_by
            ).order_by('created_at').first()
            
            if first_comment:
                response_time = first_comment.created_at - ticket.created_at
                total_response_time += response_time.total_seconds() / 3600  # Convert to hours
                response_count += 1
        
        context['avg_response_time'] = total_response_time / max(response_count, 1)
        
        # SLA breaches - this assumes you've implemented SLA breach tracking
        context['sla_breaches'] = Ticket.objects.filter(
            Q(due_date__lt=now) & 
            ~Q(status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED])
        ).count()
        
        # Ticket counts by status
        status_counts = {}
        for status, _ in Ticket.Status.choices:
            status_counts[status] = Ticket.objects.filter(status=status).count()
        
        context['ticket_counts'] = status_counts
        
        # Tickets by category
        context['tickets_by_category'] = Ticket.objects.values(
            'category__name'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Weekly ticket trends
        # Get labels for the last 7 days
        labels = []
        created_counts = []
        resolved_counts = []
        
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            day_label = day.strftime('%a')
            labels.append(day_label)
            
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            created_counts.append(
                Ticket.objects.filter(created_at__range=(day_start, day_end)).count()
            )
            
            resolved_counts.append(
                Ticket.objects.filter(
                    status=Ticket.Status.RESOLVED, 
                    resolved_at__range=(day_start, day_end)
                ).count()
            )
        
        context['weekly_labels'] = json.dumps(labels)
        context['weekly_created'] = json.dumps(created_counts)
        context['weekly_resolved'] = json.dumps(resolved_counts)
        
        # Agent performance
        agent_performance = []
        agents = User.objects.filter(user_type='agent')
        
        for agent in agents:
            # Get assigned and resolved counts
            assigned_count = Ticket.objects.filter(assigned_to=agent).count()
            resolved_count = Ticket.objects.filter(
                assigned_to=agent,
                status=Ticket.Status.RESOLVED
            ).count()
            
            # Calculate average response time for agent
            agent_tickets = Ticket.objects.filter(assigned_to=agent, created_at__gte=month_ago)
            
            agent_response_time = 0
            agent_response_count = 0
            
            for ticket in agent_tickets:
                # Get the earliest comment by this agent
                first_agent_comment = Comment.objects.filter(
                    content_type=ticket_type,
                    object_id=ticket.id,
                    author=agent
                ).order_by('created_at').first()
                
                if first_agent_comment:
                    response_time = first_agent_comment.created_at - ticket.created_at
                    agent_response_time += response_time.total_seconds() / 3600  # Convert to hours
                    agent_response_count += 1
            
            avg_response = agent_response_time / max(agent_response_count, 1)
            
            # Calculate average resolution time
            resolved_tickets = Ticket.objects.filter(
                assigned_to=agent,
                status=Ticket.Status.RESOLVED,
                resolved_at__isnull=False
            )
            
            resolution_time = 0
            resolution_count = 0
            
            for ticket in resolved_tickets:
                if ticket.resolved_at and ticket.created_at:
                    time_to_resolve = ticket.resolved_at - ticket.created_at
                    resolution_time += time_to_resolve.total_seconds() / 3600  # Convert to hours
                    resolution_count += 1
            
            avg_resolution = resolution_time / max(resolution_count, 1)
            
            # For this example, we'll use a placeholder for customer ratings
            # In a real application, you would have a rating model associated with tickets
            rating = random.uniform(3.5, 5.0)
            
            agent_performance.append({
                'name': agent.get_full_name() or agent.username,
                'assigned': assigned_count,
                'resolved': resolved_count,
                'avg_response': avg_response,
                'avg_resolution': avg_resolution,
                'rating': rating
            })
        
        context['agent_performance'] = sorted(
            agent_performance, 
            key=lambda x: x['resolved'], 
            reverse=True
        )
        
        # Branch performance
        branch_performance = []
        
        for branch_code, branch_name in Ticket.Branch.choices:
            # Get open and resolved counts
            branch_open = open_tickets.filter(branch=branch_code).count()
            branch_resolved = Ticket.objects.filter(
                branch=branch_code,
                status=Ticket.Status.RESOLVED
            ).count()
            
            # Calculate average resolution time
            branch_resolved_tickets = Ticket.objects.filter(
                branch=branch_code,
                status=Ticket.Status.RESOLVED,
                resolved_at__isnull=False
            )
            
            branch_resolution_time = 0
            branch_resolution_count = 0
            
            for ticket in branch_resolved_tickets:
                if ticket.resolved_at and ticket.created_at:
                    time_to_resolve = ticket.resolved_at - ticket.created_at
                    branch_resolution_time += time_to_resolve.total_seconds() / 3600
                    branch_resolution_count += 1
            
            avg_resolution = branch_resolution_time / max(branch_resolution_count, 1)
            
            # Calculate SLA compliance
            # For branches, we'll use tickets with due dates as a proxy for SLA
            total_branch_tickets = Ticket.objects.filter(
                branch=branch_code,
                created_at__gte=month_ago,
                due_date__isnull=False
            ).count()
            
            overdue_tickets = Ticket.objects.filter(
                branch=branch_code,
                created_at__gte=month_ago,
                due_date__lt=now,
                status__in=[Ticket.Status.NEW, Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING]
            ).count()
            
            if total_branch_tickets > 0:
                sla_compliance = round(((total_branch_tickets - overdue_tickets) / total_branch_tickets) * 100)
            else:
                sla_compliance = 100
            
            branch_performance.append({
                'name': branch_name,
                'open': branch_open,
                'resolved': branch_resolved,
                'avg_resolution': avg_resolution,
                'sla_compliance': sla_compliance
            })
        
        context['branch_performance'] = sorted(
            branch_performance, 
            key=lambda x: x['sla_compliance'], 
            reverse=True
        )
        
        # SLA compliance by priority
        sla_compliance = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0
        }
        
        for priority, _ in Ticket.Priority.choices:
            total_priority_tickets = Ticket.objects.filter(
                priority=priority,
                created_at__gte=month_ago,
                due_date__isnull=False
            ).count()
            
            overdue_tickets = Ticket.objects.filter(
                priority=priority,
                created_at__gte=month_ago,
                due_date__lt=now,
                status__in=[Ticket.Status.NEW, Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING]
            ).count()
            
            if total_priority_tickets > 0:
                compliance = round(((total_priority_tickets - overdue_tickets) / total_priority_tickets) * 100)
            else:
                compliance = 100
            
            sla_compliance[priority] = compliance
        
        context['sla_compliance'] = sla_compliance
        
        # Recent activities
        # Combining ticket history and comments for activity feed
        recent_activities = []
        
        # Get recent ticket status changes
        ticket_history = TicketHistory.objects.filter(
            field_changed='status'
        ).select_related('ticket', 'user').order_by('-timestamp')[:10]
        
        for history in ticket_history:
            recent_activities.append({
                'timestamp': history.timestamp,
                'title': f"Ticket #{history.ticket.id}: {history.ticket.title}",
                'description': f"Status changed from '{history.old_value}' to '{history.new_value}'",
                'user': history.user.get_full_name() or history.user.username
            })
        
        # Get recent comments
        recent_comments = Comment.objects.filter(
            content_type=ticket_type
        ).select_related('author').order_by('-created_at')[:10]
        
        for comment in recent_comments:
            try:
                # Try to get the ticket
                ticket = Ticket.objects.get(id=comment.object_id)
                recent_activities.append({
                    'timestamp': comment.created_at,
                    'title': f"Comment on Ticket #{ticket.id}: {ticket.title}",
                    'description': comment.text[:100] + ('...' if len(comment.text) > 100 else ''),
                    'user': comment.author.get_full_name() or comment.author.username if comment.author else 'Anonymous'
                })
            except Ticket.DoesNotExist:
                # Skip if ticket doesn't exist
                continue
        
        # Sort activities by timestamp
        recent_activities = sorted(
            recent_activities,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:10]  # Limit to 10 most recent
        
        context['recent_activities'] = recent_activities
        
        # Critical issues
        context['critical_issues'] = Ticket.objects.filter(
            priority=Ticket.Priority.CRITICAL,
            status__in=[
                Ticket.Status.NEW,
                Ticket.Status.OPEN,
                Ticket.Status.IN_PROGRESS,
                Ticket.Status.WAITING
            ]
        ).select_related('assigned_to').order_by('-created_at')[:5]
        
        return context
    
    def get_customer_dashboard(self, context, user):
        """Generate a simplified dashboard for customers"""
        # Time periods for filtering
        now = timezone.now()
        ticket_type = ContentType.objects.get_for_model(Ticket)
        
        # User's tickets
        user_tickets = Ticket.objects.filter(created_by=user)
        context['user_tickets'] = user_tickets
        
        # Ticket counts by status
        context['tickets_by_status'] = user_tickets.values(
            'status'
        ).annotate(count=Count('id'))
        
        # Recent activities on user's tickets
        recent_activities = []
        
        # Get status changes on user's tickets
        ticket_history = TicketHistory.objects.filter(
            ticket__created_by=user,
            field_changed='status'
        ).select_related('ticket', 'user').order_by('-timestamp')[:10]
        
        for history in ticket_history:
            recent_activities.append({
                'timestamp': history.timestamp,
                'title': f"Ticket #{history.ticket.id}: {history.ticket.title}",
                'description': f"Status changed from '{history.old_value}' to '{history.new_value}'",
                'user': history.user.get_full_name() or history.user.username
            })
        
        # Get recent comments on user's tickets
        user_ticket_ids = user_tickets.values_list('id', flat=True)
        
        # Directly query for comments on the user's tickets
        recent_comments = Comment.objects.filter(
            content_type=ticket_type,
            object_id__in=user_ticket_ids
        ).select_related('author').order_by('-created_at')[:10]
        
        for comment in recent_comments:
            try:
                # Try to get the ticket
                ticket = Ticket.objects.get(id=comment.object_id)
                # Skip user's own comments
                if comment.author == user:
                    continue
                    
                recent_activities.append({
                    'timestamp': comment.created_at,
                    'title': f"New reply on Ticket #{ticket.id}: {ticket.title}",
                    'description': comment.text[:100] + ('...' if len(comment.text) > 100 else ''),
                    'user': comment.author.get_full_name() or comment.author.username if comment.author else 'Anonymous'
                })
            except Ticket.DoesNotExist:
                # Skip if ticket doesn't exist
                continue
        
        # Sort activities by timestamp
        recent_activities = sorted(
            recent_activities,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:5]  # Limit to 5 most recent
        
        context['recent_activities'] = recent_activities
        
        return context
    
@login_required
@user_passes_test(lambda u: u.is_staff)
def email_settings(request):
    """Manage email notification settings"""
    # Get or create default settings
    settings, created = EmailSetting.objects.get_or_create(
        name="Default",
        defaults={
            "description": "Default email notification settings",
            "is_enabled": True,
        }
    )
    
    if request.method == 'POST':
        # Update settings
        settings.is_enabled = request.POST.get('is_enabled') == 'on'
        settings.email_signature = request.POST.get('email_signature', '')
        
        # Agent notifications
        settings.notify_all_agents_on_new_ticket = request.POST.get('notify_all_agents_on_new_ticket') == 'on'
        settings.notify_selected_agents_only = request.POST.get('notify_selected_agents_only') == 'on'
        settings.notify_agent_on_assignment = request.POST.get('notify_agent_on_assignment') == 'on'
        settings.notify_agent_on_comment = request.POST.get('notify_agent_on_comment') == 'on'
        
        # Customer notifications
        settings.notify_customer_on_ticket_created = request.POST.get('notify_customer_on_ticket_created') == 'on'
        settings.notify_customer_on_status_change = request.POST.get('notify_customer_on_status_change') == 'on'
        settings.notify_customer_on_comment = request.POST.get('notify_customer_on_comment') == 'on'
        
        settings.save()
        
        # Handle selected agents
        if settings.notify_selected_agents_only:
            selected_agent_ids = request.POST.getlist('selected_agents')
            settings.selected_agents.clear()
            settings.selected_agents.add(*selected_agent_ids)
        
        messages.success(request, _("Email settings updated successfully."))
        return redirect('core:email-settings')
    
    # Get all agents for selection
    agents = User.objects.filter(user_type=User.UserType.AGENT)
    
    context = {
        'settings': settings,
        'agents': agents,
        'selected_agent_ids': list(settings.selected_agents.values_list('id', flat=True)),
    }
    return render(request, 'core/email_settings.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def email_logs(request):
    """View email notification logs"""
    # Get filter parameters
    email_type = request.GET.get('email_type')
    status = request.GET.get('status')
    recipient = request.GET.get('recipient')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    # Base queryset
    logs = EmailLog.objects.all().order_by('-created_at')
    
    # Apply filters
    if email_type:
        logs = logs.filter