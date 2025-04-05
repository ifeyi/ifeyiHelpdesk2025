"""
WSGI config for helpdesk project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys

# Add the parent directory to sys.path to find helpdesk_app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helpdesk.settings')

application = get_wsgi_application()