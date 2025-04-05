from django.http import HttpResponse
from .models import User, AgentProfile
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme

# Simple placeholder views
def profile(request):
    return HttpResponse("User Profile")

def agent_list(request):
    return HttpResponse("Agent List")

def agent_detail(request, pk):
    return HttpResponse(f"Agent Detail for {pk}")

def ldap_login(request):
    """
    LDAP authentication view for the helpdesk system.
    Handles redirecting to the original requested page after login.
    """
    # Get the URL to redirect to after login
    next_url = request.GET.get('next', '/')
    
    # Determine if the next_url is safe (from the same site)
    is_safe_url = url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )
    
    # If not safe, default to home
    if not is_safe_url:
        next_url = '/'
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _('You have successfully logged in.'))
                
                # Redirect to the original requested page
                redirect_url = request.POST.get('next', next_url)
                return redirect(redirect_url)
            else:
                messages.error(request, _('Invalid username or password.'))
        else:
            messages.error(request, _('Please provide both username and password.'))
    
    context = {
        'redirect_field_name': 'next',
        'redirect_field_value': next_url,
    }
    
    return render(request, 'accounts/ldap_login.html', context)