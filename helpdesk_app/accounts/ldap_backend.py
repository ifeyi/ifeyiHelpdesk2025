# Create this file at: accounts/ldap_backend.py

import ldap
import logging
from django.dispatch import receiver
from django_auth_ldap.backend import LDAPBackend, populate_user
from django.contrib.auth import get_user_model
from .models import AgentProfile, CustomerProfile

User = get_user_model()
logger = logging.getLogger('accounts.ldap_backend')

@receiver(populate_user)
def process_ldap_user(sender, user=None, ldap_user=None, **kwargs):
    """
    Process the user after LDAP authentication and before saving to the database.
    This hook allows us to set the user_type and create appropriate profiles.
    """
    if not user or not ldap_user:
        return
    
    logger.debug(f"Processing LDAP user: {user.username}")
    
    # Determine user type based on group membership
    # Mapping of user types to their corresponding AD groups
    user_type_mapping = {
        User.UserType.ADMIN: ["CN=Super Users,OU=CFC-Users,DC=creditfoncier,DC=cm"],
        User.UserType.AGENT: ["CN=Staff Users,OU=CFC-Users,DC=creditfoncier,DC=cm"],
        User.UserType.CUSTOMER: ["CN=Active Users,OU=CFC-Users,DC=creditfoncier,DC=cm"],
    }
    
    # Get group DNs for this user
    if hasattr(ldap_user, 'group_dns'):
        user_groups = ldap_user.group_dns
        logger.debug(f"User groups: {user_groups}")
        
        # Determine user type based on group membership
        for user_type, group_dns in user_type_mapping.items():
            if any(group_dn in user_groups for group_dn in group_dns):
                user.user_type = user_type
                logger.debug(f"Setting user type to: {user_type}")
                break
        else:
            # Default to customer if no matching groups
            user.user_type = User.UserType.CUSTOMER
            logger.debug("No matching groups found, defaulting to Customer")
    
    # Extract department from LDAP if available
    if hasattr(ldap_user, 'attrs'):
        if 'department' in ldap_user.attrs:
            user.department = ldap_user.attrs['department'][0].decode('utf-8')
        
        if 'telephoneNumber' in ldap_user.attrs:
            user.phone = ldap_user.attrs['telephoneNumber'][0].decode('utf-8')
    
    # Save the user after modifications
    user.save()
    
    # Create appropriate profile based on user_type if it doesn't exist
    if user.user_type == User.UserType.AGENT and not hasattr(user, 'agent_profile'):
        AgentProfile.objects.get_or_create(user=user)
        logger.debug(f"Created agent profile for {user.username}")
    
    elif user.user_type == User.UserType.CUSTOMER and not hasattr(user, 'customer_profile'):
        # For customers, try to extract company/account info from LDAP
        company = ""
        account_id = ""
        support_level = "Standard"
        
        if hasattr(ldap_user, 'attrs'):
            if 'company' in ldap_user.attrs:
                company = ldap_user.attrs['company'][0].decode('utf-8')
                
            # You might use custom AD attributes for account_id and support_level
            if 'extensionAttribute1' in ldap_user.attrs:  # Example custom attribute for account_id
                account_id = ldap_user.attrs['extensionAttribute1'][0].decode('utf-8')
                
            if 'extensionAttribute2' in ldap_user.attrs:  # Example custom attribute for support_level
                support_level = ldap_user.attrs['extensionAttribute2'][0].decode('utf-8')
        
        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                'company': company,
                'account_id': account_id,
                'support_level': support_level
            }
        )
        logger.debug(f"Created customer profile for {user.username}")

class CustomLDAPBackend(LDAPBackend):
    """
    Custom LDAP backend that properly handles existing users.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # First check if this user already exists in our database
        try:
            existing_user = User.objects.get(username=username)
            logger.debug(f"Found existing user in database: {username}")
            
            # If user exists, authenticate against LDAP but don't try to create a new user
            if self._authenticate_user_dn(existing_user.username, password):
                logger.debug(f"LDAP authentication successful for existing user: {username}")
                return existing_user
            else:
                logger.debug(f"LDAP authentication failed for existing user: {username}")
                return None
                
        except User.DoesNotExist:
            # If user doesn't exist yet, use the standard LDAP backend to create them
            logger.debug(f"User {username} doesn't exist yet, using standard LDAP backend")
            return super().authenticate(request, username=username, password=password, **kwargs)
    
    def _authenticate_user_dn(self, username, password):
        """
        Attempt to bind with the user's DN and password.
        """
        try:
            # Initialize a new connection to LDAP
            from django.conf import settings
            server_uri = settings.AUTH_LDAP_SERVER_URI
            bind_dn = settings.AUTH_LDAP_BIND_DN
            bind_password = settings.AUTH_LDAP_BIND_PASSWORD
            
            # Connect with service account
            connection = ldap.initialize(server_uri)
            for opt, value in settings.AUTH_LDAP_CONNECTION_OPTIONS.items():
                connection.set_option(opt, value)
            
            # Bind with service account
            connection.simple_bind_s(bind_dn, bind_password)
            
            # Search for the user
            search_base = "OU=CFC-Users,DC=creditfoncier,DC=cm"  # Use same base as in settings
            search_filter = f"(sAMAccountName={username})"
            
            # Find the user's DN
            results = connection.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter, ['dn'])
            connection.unbind_s()  # Close the service account connection
            
            if not results:
                logger.error(f"User {username} not found in LDAP")
                return False
                
            user_dn = results[0][0]  # Extract the DN
            
            # Try to bind with the user's credentials
            user_connection = ldap.initialize(server_uri)
            for opt, value in settings.AUTH_LDAP_CONNECTION_OPTIONS.items():
                user_connection.set_option(opt, value)
                
            # Try to bind - this validates the password
            user_connection.simple_bind_s(user_dn, password)
            user_connection.unbind_s()  # Clean up
            
            # If we get here, authentication was successful
            logger.debug(f"Successfully authenticated {username} with DN: {user_dn}")
            return True
            
        except ldap.INVALID_CREDENTIALS:
            logger.error(f"Invalid credentials for user: {username}")
            return False
        except Exception as e:
            logger.error(f"LDAP authentication error for {username}: {str(e)}")
            return False