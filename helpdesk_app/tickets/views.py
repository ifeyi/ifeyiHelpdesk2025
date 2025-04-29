from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, F
from django.db import models
from .models import Ticket, Category, Tag, TicketAttachment, TicketHistory, Department, SubDepartment
from accounts.models import User
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from comments.models import Comment
from django.http import JsonResponse

@login_required
def ticket_list(request):
    """
    Display a list of tickets.
    For customers: Only shows their own tickets
    For agents/staff: Shows tickets based on filters
    """
    # Base queryset
    tickets = Ticket.objects.all().select_related('created_by', 'assigned_to', 'category', 'department', 'subdepartment')
    
    # Filter by user type
    if not request.user.is_staff and not hasattr(request.user, 'agent_profile'):
        # Customer view - only their tickets
        tickets = tickets.filter(created_by=request.user)
    
    # Apply filters if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    
    branch_filter = request.GET.get('branch')
    if branch_filter and branch_filter != 'all':
        tickets = tickets.filter(branch=branch_filter)

    priority_filter = request.GET.get('priority')
    if priority_filter and priority_filter != 'all':
        tickets = tickets.filter(priority=priority_filter)
    
    category_filter = request.GET.get('category')
    if category_filter and category_filter.isdigit():
        tickets = tickets.filter(category_id=category_filter)
    
    # Department filter
    department_filter = request.GET.get('department')
    if department_filter and department_filter.isdigit():
        tickets = tickets.filter(department_id=department_filter)
    
    # Sub-department filter
    subdepartment_filter = request.GET.get('subdepartment')
    if subdepartment_filter and subdepartment_filter.isdigit():
        tickets = tickets.filter(subdepartment_id=subdepartment_filter)
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Get filter options
    categories = Category.objects.all()
    departments = Department.objects.all().prefetch_related('subdepartments')
    
    context = {
        'tickets': tickets,
        'status_choices': Ticket.Status.choices,
        'branch_choices': Ticket.Branch.choices,
        'priority_choices': Ticket.Priority.choices,
        'categories': categories,
        'departments': departments,
        'current_status': status_filter,
        'current_branch': branch_filter,
        'current_priority': priority_filter,
        'current_category': category_filter,
        'current_department': department_filter,
        'current_subdepartment': subdepartment_filter,
        'search_query': search_query,
    }
    
    return render(request, 'tickets/ticket_list.html', context)

@login_required
def ticket_detail(request, pk):
    """Display a single ticket with all its details and comments"""

    # For staff, get any ticket; for customers, only their own tickets
    if request.user.is_staff or hasattr(request.user, 'agent_profile'):
        ticket = get_object_or_404(Ticket.objects.select_related(
            'created_by', 'assigned_to', 'category', 'department', 'subdepartment'), pk=pk)
    else:
        ticket = get_object_or_404(Ticket.objects.select_related(
            'created_by', 'assigned_to', 'category', 'department', 'subdepartment'), 
            pk=pk, created_by=request.user)
        
    ticket_type = ContentType.objects.get_for_model(Ticket)
    comments = Comment.objects.filter(
        content_type=ticket_type,
        object_id=ticket.id
    ).select_related('author').prefetch_related('attachments')
    
    # Non-staff can only see non-internal comments
    if not (request.user.is_staff or hasattr(request.user, 'agent_profile')):
        comments = comments.filter(is_internal=False)
    
    # Get available agents if user is staff or admin
    agents = None
    if request.user.is_staff or request.user.is_admin:
        agents = User.objects.filter(
            user_type=User.UserType.AGENT
        ).select_related(
            'agent_profile'
        ).prefetch_related(
            'assigned_tickets',
            'agent_profile__expertise'
        ).order_by('first_name', 'last_name')
    
    # Get last edit information
    last_edit = TicketHistory.objects.filter(ticket=ticket).order_by('-timestamp').first()
    
    context = {
        'ticket': ticket,
        'agents': agents,
        'comments': comments,
        'user_is_staff': request.user.is_staff or hasattr(request.user, 'agent_profile'),
        'last_edit': last_edit,
    }
    return render(request, 'tickets/ticket_detail.html', context)

@login_required
def ticket_create(request):
    
    parent_categories = Category.objects.filter(parent__isnull=True)
    categories = Category.objects.all()
    departments = Department.objects.all().prefetch_related('subdepartments')
    
    if request.method == 'POST':
        # Process the form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        branch = request.POST.get('branch')
        priority = request.POST.get('priority')
        office_door_number = request.POST.get('office_door_number')
        department_id = request.POST.get('department')
        subdepartment_id = request.POST.get('subdepartment')

        # Validate required fields
        if not title or not description:
            messages.error(request, _("Please fill out all required fields."))
            context = {
                'parent_categories': parent_categories,
                'categories': categories,
                'departments': departments,
                'branch_choices': Ticket.Branch.choices,
                'priority_choices': Ticket.Priority.choices,
                'form_data': request.POST,  # Return form data for repopulation
            }
            return render(request, 'tickets/ticket_create.html', context)
        
        # Create the ticket
        ticket = Ticket.objects.create(
            title=title,
            description=description,
            branch=branch or Ticket.Branch.SIEGE,
            priority=priority or Ticket.Priority.MEDIUM,
            created_by=request.user,
            status=Ticket.Status.NEW,
            office_door_number=office_door_number,
        )
        
        # Set category if provided
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                ticket.category = category
                ticket.save()
            except Category.DoesNotExist:
                pass
        
        # Set department if provided
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
                ticket.department = department
                # Record in history
                TicketHistory.objects.create(
                    ticket=ticket,
                    user=request.user,
                    field_changed='department',
                    old_value='',
                    new_value=str(department)
                )
            except Department.DoesNotExist:
                pass
        
        # Set subdepartment if provided
        if subdepartment_id:
            try:
                subdepartment = SubDepartment.objects.get(id=subdepartment_id)
                # Check if subdepartment belongs to selected department
                if not department_id or subdepartment.department_id == int(department_id):
                    ticket.subdepartment = subdepartment
                    # Record in history
                    TicketHistory.objects.create(
                        ticket=ticket,
                        user=request.user,
                        field_changed='subdepartment',
                        old_value='',
                        new_value=str(subdepartment)
                    )
            except SubDepartment.DoesNotExist:
                pass
        
        ticket.save()
        
        # Handle file attachments
        files = request.FILES.getlist('file')
        for file in files:
            TicketAttachment.objects.create(
                ticket=ticket,
                file=file,
                uploaded_by=request.user,
                description=file.name
            )
        
        # Create ticket history entry
        TicketHistory.objects.create(
            ticket=ticket,
            user=request.user,
            field_changed='status',
            old_value='',
            new_value=ticket.get_status_display()
        )
        
        messages.success(request, _(f"Ticket #{ticket.id} created successfully."))
        return redirect('tickets:ticket-detail', pk=ticket.pk)
    
    # If not POST, just render the form
    context = {
        'parent_categories': parent_categories,
        'categories': categories,
        'departments': departments,
        'branch_choices': Ticket.Branch.choices,
        'priority_choices': Ticket.Priority.choices,
    }
    return render(request, 'tickets/ticket_create.html', context)

@login_required
def ticket_update(request, pk):
    """Update an existing ticket"""
    # For staff, get any ticket; for customers, only their own tickets
    if request.user.is_staff or hasattr(request.user, 'agent_profile'):
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        ticket = get_object_or_404(Ticket, pk=pk, created_by=request.user)

    parent_categories = Category.objects.filter(parent__isnull=True)
    categories = Category.objects.all()
    departments = Department.objects.all().prefetch_related('subdepartments')
    
    if request.method == 'POST':
        # Process the form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        branch = request.POST.get('branch')
        priority = request.POST.get('priority')
        status = request.POST.get('status')
        office_door_number = request.POST.get('office_door_number')
        department_id = request.POST.get('department')
        subdepartment_id = request.POST.get('subdepartment')
        
        # Validate required fields
        if not title or not description:
            messages.error(request, _("Please fill out all required fields."))
            context = {
                'ticket': ticket,
                'parent_categories': parent_categories,
                'categories': categories,
                'departments': departments,
                'branch_choices': Ticket.Branch.choices,
                'priority_choices': Ticket.Priority.choices,
                'status_choices': Ticket.Status.choices,
            }
            return render(request, 'tickets/ticket_update.html', context)
        
        # Track changes for history
        changes = []
        if ticket.title != title:
            changes.append(('title', ticket.title, title))
            ticket.title = title
            
        if ticket.description != description:
            changes.append(('description', ticket.description, description))
            ticket.description = description
            
        if ticket.office_door_number != office_door_number:
            changes.append(('office_door_number', 
                        ticket.office_door_number or _('None'), 
                        office_door_number or _('None')))
            ticket.office_door_number = office_door_number

        old_category = ticket.category
        if category_id and (not old_category or str(old_category.id) != category_id):
            try:
                new_category = Category.objects.get(id=category_id)
                ticket.category = new_category
                changes.append(('category', 
                                str(old_category) if old_category else 'None', 
                                str(new_category)))
            except Category.DoesNotExist:
                pass

        # Department changes
        old_department = ticket.department
        if department_id and (not old_department or str(old_department.id) != department_id):
            try:
                new_department = Department.objects.get(id=department_id)
                ticket.department = new_department
                changes.append(('department', 
                                str(old_department) if old_department else 'None', 
                                str(new_department)))
                
                # If department changes, reset subdepartment unless it belongs to the new department
                if ticket.subdepartment and ticket.subdepartment.department_id != new_department.id:
                    old_subdept = ticket.subdepartment
                    ticket.subdepartment = None
                    changes.append(('subdepartment', 
                                    str(old_subdept) if old_subdept else 'None', 
                                    'None'))
            except Department.DoesNotExist:
                pass
        elif not department_id and old_department:
            # Removing department assignment
            changes.append(('department', str(old_department), 'None'))
            ticket.department = None
            
            # Also remove subdepartment if department is removed
            if ticket.subdepartment:
                old_subdept = ticket.subdepartment
                ticket.subdepartment = None
                changes.append(('subdepartment', str(old_subdept), 'None'))

        # Subdepartment changes
        old_subdepartment = ticket.subdepartment
        if subdepartment_id and (not old_subdepartment or str(old_subdepartment.id) != subdepartment_id):
            try:
                new_subdepartment = SubDepartment.objects.get(id=subdepartment_id)
                # Make sure the subdepartment belongs to the selected department
                if ticket.department and new_subdepartment.department_id == ticket.department.id:
                    ticket.subdepartment = new_subdepartment
                    changes.append(('subdepartment', 
                                    str(old_subdepartment) if old_subdepartment else 'None', 
                                    str(new_subdepartment)))
            except SubDepartment.DoesNotExist:
                pass
        elif not subdepartment_id and old_subdepartment:
            # Removing subdepartment assignment
            changes.append(('subdepartment', str(old_subdepartment), 'None'))
            ticket.subdepartment = None

        if ticket.branch != branch:
            changes.append(('branch', ticket.get_branch_display(), dict(Ticket.Branch.choices)[branch]))
            ticket.branch = branch

        if ticket.priority != priority:
            changes.append(('priority', 
                           ticket.get_priority_display(), 
                           dict(Ticket.Priority.choices)[priority]))
            ticket.priority = priority
            
        # Status changes - only staff/agents can change status
        if (request.user.is_staff or hasattr(request.user, 'agent_profile')) and status and ticket.status != status:
            old_status_display = ticket.get_status_display()
            ticket.status = status
            new_status_display = dict(Ticket.Status.choices)[status]
            changes.append(('status', old_status_display, new_status_display))
            
            # Update relevant timestamps based on status
            from django.utils import timezone
            now = timezone.now()
            
            if status == Ticket.Status.RESOLVED and not ticket.resolved_at:
                ticket.resolved_at = now
            elif status == Ticket.Status.CLOSED and not ticket.closed_at:
                ticket.closed_at = now
        
        # Save the ticket
        ticket.save()
        
        # Record history for each change
        for field, old_value, new_value in changes:
            TicketHistory.objects.create(
                ticket=ticket,
                user=request.user,
                field_changed=field,
                old_value=old_value,
                new_value=new_value
            )
        
        # Handle file attachments
        files = request.FILES.getlist('file')
        for file in files:
            TicketAttachment.objects.create(
                ticket=ticket,
                file=file,
                uploaded_by=request.user,
                description=file.name
            )
        
        messages.success(request, f"Ticket #{ticket.id} updated successfully.")
        return redirect('tickets:ticket-detail', pk=ticket.pk)
    
    # If not POST, render the form with existing data
    context = {
        'ticket': ticket,
        'parent_categories': parent_categories,
        'categories': categories,
        'departments': departments,
        'branch_choices': Ticket.Branch.choices,
        'priority_choices': Ticket.Priority.choices,
        'status_choices': Ticket.Status.choices,
    }
    return render(request, 'tickets/ticket_update.html', context)

@login_required
def ticket_delete(request, pk):
    """Delete a ticket"""
    # Only staff or the creator can delete tickets
    if request.user.is_staff or hasattr(request.user, 'agent_profile'):
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        ticket = get_object_or_404(Ticket, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        ticket_id = ticket.id
        ticket.delete()
        messages.success(request, _(f"Ticket #{ticket_id} has been deleted."))
        return redirect('tickets:ticket-list')
    
    # Confirm deletion
    context = {
        'ticket': ticket,
    }
    return render(request, 'tickets/ticket_delete.html', context)

@login_required
def ticket_change_status(request, pk):
    """Quick status change for a ticket"""
    # Only staff or agents can change status
    if not (request.user.is_staff or hasattr(request.user, 'agent_profile')):
        messages.error(request, _("You don't have permission to change ticket status."))
        return redirect('tickets:ticket-list')
    
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Ticket.Status.choices):
            old_status = ticket.status
            old_status_display = ticket.get_status_display()
            
            # Update the status
            ticket.status = new_status
            
            # Update relevant timestamps
            from django.utils import timezone
            now = timezone.now()
            
            if new_status == Ticket.Status.RESOLVED and not ticket.resolved_at:
                ticket.resolved_at = now
            elif new_status == Ticket.Status.CLOSED and not ticket.closed_at:
                ticket.closed_at = now
            
            ticket.save()
            
            # Record the change in history
            TicketHistory.objects.create(
                ticket=ticket,
                user=request.user,
                field_changed='status',
                old_value=old_status_display,
                new_value=dict(Ticket.Status.choices)[new_status]
            )
            
            messages.success(request, _(f"Ticket status updated to {dict(Ticket.Status.choices)[new_status]}."))
        else:
            messages.error(request, _("Invalid status selected."))
    
    return redirect('tickets:ticket-detail', pk=pk)

@login_required
def ticket_assign(request, pk):
    """Assign a ticket to an agent"""
    # Only staff or admins can assign tickets
    if not (request.user.is_staff or request.user.is_admin):
        messages.error(request, _("You don't have permission to assign tickets."))
        return redirect('tickets:ticket-list')
    
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        agent_id = request.POST.get('agent')
        
        if agent_id:
            try:
                agent = User.objects.get(id=agent_id, user_type=User.UserType.AGENT)
                
                # Record the old assigned agent (if any)
                old_agent = ticket.assigned_to
                old_agent_str = str(old_agent) if old_agent else 'Unassigned'
                
                # Update the ticket
                ticket.assigned_to = agent
                ticket.status = Ticket.Status.OPEN  # Automatically set to open when assigned
                ticket.save()
                
                # Record in history
                TicketHistory.objects.create(
                    ticket=ticket,
                    user=request.user,
                    field_changed='assigned_to',
                    old_value=old_agent_str,
                    new_value=str(agent)
                )
                
                # Also record status change if it happened
                if ticket.status != Ticket.Status.OPEN:
                    TicketHistory.objects.create(
                        ticket=ticket,
                        user=request.user,
                        field_changed='status',
                        old_value=ticket.get_status_display(),
                        new_value=dict(Ticket.Status.choices)[Ticket.Status.OPEN]
                    )
                
                messages.success(request, _(f"Ticket #{ticket.id} assigned to {agent.get_full_name() or agent.email}."))
            except User.DoesNotExist:
                messages.error(request, _("Selected agent does not exist."))
        else:
            # Unassign the ticket
            if ticket.assigned_to:
                old_agent = str(ticket.assigned_to)
                ticket.assigned_to = None
                ticket.save()
                
                # Record in history
                TicketHistory.objects.create(
                    ticket=ticket,
                    user=request.user,
                    field_changed='assigned_to',
                    old_value=old_agent,
                    new_value='Unassigned'
                )
                
                messages.success(request, _(f"Ticket #{ticket.id} has been unassigned."))
    
    return redirect('tickets:ticket-detail', pk=pk)

def find_available_agent(ticket):
    """
    Find the most suitable agent for a ticket based on:
    1. Expertise (matches ticket category)
    2. Current workload (under max_tickets)
    3. Availability status
    
    Returns None if no suitable agent is found.
    """
    # Start with all agents
    agents_query = User.objects.filter(
        user_type=User.UserType.AGENT,
        agent_profile__availability_status=True
    ).select_related('agent_profile')
    
    # If ticket has a category, prioritize agents with expertise
    if ticket.category:
        # First try agents with matching expertise
        expert_agents = agents_query.filter(
            agent_profile__expertise=ticket.category
        ).annotate(
            ticket_count=models.Count('assigned_tickets')
        ).filter(
            ticket_count__lt=models.F('agent_profile__max_tickets')
        ).order_by('ticket_count')
        
        if expert_agents.exists():
            return expert_agents.first()
    
    # If no expert agents or no category, find any available agent
    available_agents = agents_query.annotate(
        ticket_count=models.Count('assigned_tickets')
    ).filter(
        ticket_count__lt=models.F('agent_profile__max_tickets')
    ).order_by('ticket_count')
    
    if available_agents.exists():
        return available_agents.first()
    
    return None

@login_required
def ticket_auto_assign(request, pk):
    """Automatically assign a ticket to the most suitable agent"""
    # Only staff or admins can auto-assign tickets
    if not (request.user.is_staff or request.user.is_admin):
        messages.error(request, _("You don't have permission to assign tickets."))
        return redirect('tickets:ticket-list')
    
    ticket = get_object_or_404(Ticket, pk=pk)
    
    # Find the best available agent
    agent = find_available_agent(ticket)
    
    if agent:
        # Record the old assigned agent (if any)
        old_agent = ticket.assigned_to
        old_agent_str = str(old_agent) if old_agent else 'Unassigned'
        
        # Update the ticket
        ticket.assigned_to = agent
        ticket.status = Ticket.Status.OPEN  # Automatically set to open when assigned
        ticket.save()
        
        # Record in history
        TicketHistory.objects.create(
            ticket=ticket,
            user=request.user,
            field_changed='assigned_to',
            old_value=old_agent_str,
            new_value=str(agent)
        )
        
        # Also record status change if it happened
        if ticket.status != Ticket.Status.OPEN:
            TicketHistory.objects.create(
                ticket=ticket,
                user=request.user,
                field_changed='status',
                old_value=ticket.get_status_display(),
                new_value=dict(Ticket.Status.choices)[Ticket.Status.OPEN]
            )
        
        messages.success(request, _(f"Ticket #{ticket.id} automatically assigned to {agent.get_full_name() or agent.email}."))
    else:
        messages.warning(request, _("No available agents found. Please assign manually."))
    
    return redirect('tickets:ticket-detail', pk=pk)

def get_subcategories(request, parent_id):
    """API endpoint to get subcategories for a parent category"""
    subcategories = Category.objects.filter(parent_id=parent_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

def get_subdepartments(request, department_id):
    """API endpoint to get subdepartments for a department"""
    subdepartments = SubDepartment.objects.filter(department_id=department_id).values('id', 'name')
    return JsonResponse(list(subdepartments), safe=False)