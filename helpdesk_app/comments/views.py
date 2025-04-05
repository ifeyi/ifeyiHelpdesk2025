from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Comment, CommentAttachment
from tickets.models import Ticket

@login_required
@require_POST
def add_comment(request, model_name, object_id):
    """
    Add a comment to a content object.
    Currently supports tickets.
    """
    text = request.POST.get('comment_text')  # Note: form uses 'comment_text', not 'text'
    is_internal = request.POST.get('is_internal') == 'on'  # Checkbox sends 'on' when checked
    
    # Map model names to their actual models
    model_map = {
        'ticket': Ticket,
    }
    
    if model_name not in model_map:
        messages.error(request, _("Invalid model type."))
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    model_class = model_map[model_name]
    content_type = ContentType.objects.get_for_model(model_class)
    
    try:
        content_object = model_class.objects.get(id=object_id)
    except model_class.DoesNotExist:
        messages.error(request, _("Object not found."))
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Validate text
    if not text:
        messages.error(request, _("Comment text cannot be empty."))
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Check permissions for internal comments
    if is_internal and not (request.user.is_staff or hasattr(request.user, 'agent_profile')):
        is_internal = False
    
    # Create the comment
    comment = Comment.objects.create(
        content_type=content_type,
        object_id=object_id,
        author=request.user,
        text=text,
        is_internal=is_internal
    )
    
    # Handle file attachments
    files = request.FILES.getlist('file')
    for file in files:
        CommentAttachment.objects.create(
            comment=comment,
            file=file,
            description=file.name
        )
    
    # Update ticket status if needed (for tickets)
    if model_name == 'ticket':
        ticket = content_object
        
        # If agent comments and ticket is 'waiting', change to 'in_progress'
        if (request.user.is_staff or hasattr(request.user, 'agent_profile')) and ticket.status == Ticket.Status.WAITING:
            ticket.status = Ticket.Status.IN_PROGRESS
            ticket.save()
            
        # If customer comments and ticket is 'resolved', reopen it
        elif not (request.user.is_staff or hasattr(request.user, 'agent_profile')) and ticket.status == Ticket.Status.RESOLVED:
            ticket.status = Ticket.Status.OPEN
            ticket.save()
    
    messages.success(request, _("Comment added successfully."))
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def delete_comment(request, pk):
    """
    Delete a comment.
    Users can only delete their own comments.
    Staff can delete any comment.
    """
    comment = get_object_or_404(Comment, pk=pk)
    
    # Check permission
    if not (request.user.is_staff or comment.author == request.user):
        messages.error(request, _("You don't have permission to delete this comment."))
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    if request.method == 'POST':
        # Get the parent object URL for redirect
        parent_url = request.META.get('HTTP_REFERER', '/')
        
        # Delete the comment
        comment.delete()
        
        messages.success(request, _("Comment deleted successfully."))
        return redirect(parent_url)
    
    # Confirm deletion
    context = {
        'comment': comment,
    }
    return render(request, 'comments/comment_delete.html', context)


@login_required
def edit_comment(request, pk):
    """
    Edit an existing comment.
    Users can only edit their own comments.
    Staff can edit any comment.
    """
    comment = get_object_or_404(Comment, pk=pk)
    
    # Check permission
    if not (request.user.is_staff or comment.author == request.user):
        messages.error(request, _("You don't have permission to edit this comment."))
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    if request.method == 'POST':
        text = request.POST.get('text')
        is_internal = request.POST.get('is_internal') == 'true'
        
        if not text:
            messages.error(request, _("Comment text cannot be empty."))
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Only staff/agents can post internal comments
        if is_internal and not (request.user.is_staff or hasattr(request.user, 'agent_profile')):
            is_internal = False
        
        # Update the comment
        comment.text = text
        comment.is_internal = is_internal
        comment.is_edited = True
        comment.save()
        
        # Handle file attachments
        files = request.FILES.getlist('file')
        for file in files:
            CommentAttachment.objects.create(
                comment=comment,
                file=file,
                description=file.name
            )
        
        messages.success(request, _("Comment updated successfully."))
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Show edit form
    context = {
        'comment': comment,
    }
    return render(request, 'comments/comment_edit.html', context)