import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging request and response details.
    Useful for monitoring performance and tracking API usage.
    """
    
    def process_request(self, request):
        """Store the start time of the request"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log the request and response details"""
        # Skip logging for static files and health checks
        path = request.path
        if path.startswith(settings.STATIC_URL) or path.startswith('/health/'):
            return response
        
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        else:
            duration = 0
        
        # Prepare log data
        log_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'method': request.method,
            'path': path,
            'status_code': response.status_code,
            'duration': round(duration * 1000, 2),  # Convert to milliseconds
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Log request with different levels based on status code
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
        
        return response
    
    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add various security headers to all responses.
    Helps protect against common web vulnerabilities.
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = "default-src 'self'; " \
                                             "script-src 'self' 'unsafe-inline'; " \
                                             "style-src 'self' 'unsafe-inline'; " \
                                             "img-src 'self' data:; " \
                                             "font-src 'self'; " \
                                             "connect-src 'self';"
        
        # Other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class UserActivityMiddleware(MiddlewareMixin):
    """
    Middleware to track user activity and update last active timestamp.
    Useful for tracking user engagement and activity.
    """
    
    def process_response(self, request, response):
        if request.user.is_authenticated and not request.is_ajax():
            # Skip API and AJAX requests
            if not request.path.startswith('/api/') and request.method != 'OPTIONS':
                try:
                    # Update last active timestamp - assumes the User model has this field
                    # If your User model doesn't have this field, you'll need to add it
                    request.user.last_active = time.time()
                    request.user.save(update_fields=['last_active'])
                except Exception as e:
                    logger.error(f"Error updating user activity: {str(e)}")
        
        return response