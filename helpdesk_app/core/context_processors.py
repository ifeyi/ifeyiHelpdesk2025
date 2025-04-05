from datetime import datetime

def global_context(request):
    """Add common variables to the global template context"""
    return {
        'current_year': datetime.now().year,
    }