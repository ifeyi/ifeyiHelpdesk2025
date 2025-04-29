# accounts/ldap_backend.py

import ldap
import logging
from django.dispatch import receiver
from django_auth_ldap.backend import LDAPBackend, populate_user
from django.contrib.auth import get_user_model
try:
    from .models import AgentProfile, CustomerProfile
except ImportError:
    # Handle case where models aren't loaded yet
    AgentProfile = None
    CustomerProfile = None

User = get_user_model()
logger = logging.getLogger('accounts.ldap_backend')

@receiver(populate_user)
def process_ldap_user(sender, user=None, ldap_user=None, **kwargs):

    if not user or not ldap_user:
        return
    
    logger.debug(f"Processing LDAP user: {user.username}")
    
    # Set default user_type to prevent errors
    if not hasattr(user, 'user_type') or user.user_type is None:
        user.user_type = User.UserType.CUSTOMER  # Default to customer
    
    # Make user active by default
    user.is_active = True
    
    # Determine user type based on group membership
    # Mapping of user types to their corresponding AD groups
    user_type_mapping = {
        User.UserType.ADMIN: ["CN=Super Users,OU=CFC-Users,DC=creditfoncier,DC=cm", 
                              "CN=Domain Admins,CN=Users,DC=creditfoncier,DC=cm"],
        User.UserType.AGENT: ["CN=Staff Users,OU=CFC-Users,DC=creditfoncier,DC=cm",
                              "CN=IT-ADMIN,OU=CFC-Users,DC=creditfoncier,DC=cm"],
        User.UserType.CUSTOMER: ["CN=Active Users,OU=CFC-Users,DC=creditfoncier,DC=cm",
                                "CN=Domain Users,CN=Users,DC=creditfoncier,DC=cm"],
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
            
        # Set staff and superuser status based on user_type
        if user.user_type == User.UserType.ADMIN:
            user.is_staff = True
            user.is_superuser = True
        elif user.user_type == User.UserType.AGENT:
            user.is_staff = True
            user.is_superuser = False
    
    # Extract department from LDAP if available
    if hasattr(ldap_user, 'attrs'):
        if 'department' in ldap_user.attrs:
            try:
                user.department = ldap_user.attrs['department'][0].decode('utf-8')
            except (IndexError, AttributeError):
                logger.warning(f"Could not decode department attribute for {user.username}")
        
        if 'telephoneNumber' in ldap_user.attrs:
            try:
                user.phone = ldap_user.attrs['telephoneNumber'][0].decode('utf-8')
            except (IndexError, AttributeError):
                logger.warning(f"Could not decode telephoneNumber attribute for {user.username}")
    
    # Save the user after modifications
    try:
        user.save()
    except Exception as e:
        logger.error(f"Error saving user {user.username}: {str(e)}")
        return
    
    # Import models here to avoid circular imports
    try:
        from .models import AgentProfile, CustomerProfile
    except ImportError:
        logger.error("Could not import profile models")
        return
    
    # Create appropriate profile based on user_type if it doesn't exist
    if user.user_type == User.UserType.AGENT:
        try:
            if not hasattr(user, 'agent_profile') or user.agent_profile is None:
                AgentProfile.objects.get_or_create(user=user)
                logger.debug(f"Created agent profile for {user.username}")
        except Exception as e:
            logger.error(f"Error creating agent profile for {user.username}: {str(e)}")
    
    elif user.user_type == User.UserType.CUSTOMER:
        try:
            if not hasattr(user, 'customer_profile') or user.customer_profile is None:
                # For customers, try to extract company/account info from LDAP
                company = ""
                account_id = ""
                support_level = "Standard"
                
                if hasattr(ldap_user, 'attrs'):
                    if 'company' in ldap_user.attrs:
                        try:
                            company = ldap_user.attrs['company'][0].decode('utf-8')
                        except (IndexError, AttributeError):
                            pass
                            
                    # You might use custom AD attributes for account_id and support_level
                    if 'extensionAttribute1' in ldap_user.attrs:
                        try:
                            account_id = ldap_user.attrs['extensionAttribute1'][0].decode('utf-8')
                        except (IndexError, AttributeError):
                            pass
                            
                    if 'extensionAttribute2' in ldap_user.attrs:
                        try:
                            support_level = ldap_user.attrs['extensionAttribute2'][0].decode('utf-8')
                        except (IndexError, AttributeError):
                            pass
                
                CustomerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'company': company,
                        'account_id': account_id,
                        'support_level': support_level
                    }
                )
                logger.debug(f"Created customer profile for {user.username}")
        except Exception as e:
            logger.error(f"Error creating customer profile for {user.username}: {str(e)}")


class CustomLDAPBackend(LDAPBackend):

    def authenticate(self, request=None, username=None, password=None, **kwargs):
        if not username or not password:
            logger.debug("Missing username or password")
            return None
            
        logger.debug(f"Attempting authentication for username: {username}")
        
        # Clean the username to remove domain prefixes/suffixes if present
        if '\\' in username:
            # Format is DOMAIN\username
            domain, clean_username = username.split('\\', 1)
            logger.debug(f"Extracted username '{clean_username}' from DOMAIN\\username format")
            username = clean_username
        elif '@' in username:
            # Format is username@domain
            clean_username, domain = username.split('@', 1)
            logger.debug(f"Extracted username '{clean_username}' from username@domain format")
            username = clean_username
        
        logger.debug(f"Using cleaned username for authentication: {username}")
        
        # Try different username formats
        username_formats = [
            username,  # Cleaned username
            f"{username}@creditfoncier.cm",  # UPN format
            f"CREDITFONCIER\\{username}"  # DOMAIN\username format
        ]
        
        # Remove duplicates
        unique_formats = []
        for fmt in username_formats:
            if fmt not in unique_formats:
                unique_formats.append(fmt)
        
        # Try each format
        for username_fmt in unique_formats:
            logger.debug(f"Trying authentication with username format: {username_fmt}")
            
            # Extract base username for database lookup
            base_username = username_fmt.split('@')[0].split('\\')[-1]
            
            # First check if this user already exists in our database
            try:
                existing_user = User.objects.filter(username__iexact=base_username).first()
                
                if existing_user:
                    logger.debug(f"Found existing user in database: {existing_user.username}")
                    
                    # Authenticate against LDAP
                    if self._authenticate_user_dn(base_username, password):  # Pass clean username here
                        logger.debug(f"LDAP authentication successful for existing user: {existing_user.username}")
                        # Update last_login and save
                        from django.utils import timezone
                        existing_user.last_login = timezone.now()
                        existing_user.save(update_fields=['last_login'])
                        return existing_user
                    else:
                        logger.debug(f"LDAP authentication failed for existing user: {existing_user.username}")
                        continue  # Try next format
                
                # If user doesn't exist yet, use the standard LDAP backend
                logger.debug(f"User {username_fmt} doesn't exist yet, using standard LDAP backend")
                user = super().authenticate(request, username=username_fmt, password=password, **kwargs)
                if user:
                    logger.debug(f"Created and authenticated new user: {user.username}")
                    return user
                    
            except Exception as e:
                logger.error(f"Error during authentication for {username_fmt}: {str(e)}")
                continue  # Try next format
        
        # If we've tried all formats and none worked, authentication failed
        logger.debug(f"All authentication attempts failed for: {username}")
        return None
        
def _authenticate_user_dn(self, username, password):

    try:
        # Initialize a new connection to LDAP
        from django.conf import settings
        server_uri = settings.AUTH_LDAP_SERVER_URI
        bind_dn = settings.AUTH_LDAP_BIND_DN
        bind_password = settings.AUTH_LDAP_BIND_PASSWORD
        
        logger.debug(f"Attempting LDAP authentication for {username}")
        logger.debug(f"Server URI: {server_uri}")
        # Don't log the full bind_dn and password for security
        logger.debug(f"Using service account: {bind_dn[:20]}...")
        
        if not bind_password:
            logger.error("Service account password is empty, check your secrets")
            return False
        
        # Set up connection
        connection = ldap.initialize(server_uri)
        for opt, value in settings.AUTH_LDAP_CONNECTION_OPTIONS.items():
            connection.set_option(opt, value)
        
        # Bind with service account
        try:
            connection.simple_bind_s(bind_dn, bind_password)
            logger.debug(f"Successfully bound with service account")
        except ldap.INVALID_CREDENTIALS:
            logger.error("Invalid service account credentials")
            return False
        except Exception as e:
            logger.error(f"Error binding with service account: {str(e)}")
            return False
        
        # Use a wider search base to find the user
        search_base = "DC=creditfoncier,DC=cm"  # Search from domain root
        search_filter = f"(sAMAccountName={ldap.dn.escape_dn_chars(username)})"
        
        logger.debug(f"Searching for user with filter: {search_filter}")
        logger.debug(f"Search base: {search_base}")
        
        # Find the user's DN
        try:
            results = connection.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter, ['dn'])
            
            if not results:
                logger.error(f"User {username} not found in LDAP")
                connection.unbind_s()
                return False
                
            user_dn = results[0][0]  # Extract the DN
            logger.debug(f"Found user DN: {user_dn}")
            connection.unbind_s()  # Close the service account connection
        except Exception as e:
            logger.error(f"Error searching for user {username}: {str(e)}")
            connection.unbind_s()
            return False
        
        # Try to bind with the user's credentials
        try:
            user_connection = ldap.initialize(server_uri)
            for opt, value in settings.AUTH_LDAP_CONNECTION_OPTIONS.items():
                user_connection.set_option(opt, value)
                
            # Try to bind - this validates the password
            logger.debug(f"Attempting to bind as user: {user_dn}")
            user_connection.simple_bind_s(user_dn, password)
            user_connection.unbind_s()  # Clean up
            
            # If we get here, authentication was successful
            logger.debug(f"Successfully authenticated {username} with DN: {user_dn}")
            return True
        except ldap.INVALID_CREDENTIALS:
            logger.error(f"Invalid credentials for user: {username}")
            return False
        except Exception as e:
            logger.error(f"Error binding as user {username}: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"LDAP authentication error for {username}: {str(e)}")
        return False