from django.core.management.base import BaseCommand
import ldap
import os
import sys

class Command(BaseCommand):
    help = 'Test LDAP connection and user search'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to search for')

    def handle(self, *args, **options):
        # Get the username to search for
        username = options['username']
        
        # LDAP settings (copy from your settings.py)
        server_uri = "ldap://192.168.6.90"  # Update this
        bind_dn = "CN=Ifeyi BATINDEK BATOANEN admin,OU=IT-ADMIN,OU=CFC-Users,DC=creditfoncier,DC=cm"  # Update this
        bind_password = ""  # Add your password or read from environment
        
        # LDAP Connection options
        conn_options = {
            ldap.OPT_REFERRALS: 0,
            ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
            ldap.OPT_NETWORK_TIMEOUT: 10,
            ldap.OPT_TIMEOUT: 15,
        }
        
        self.stdout.write(f"Testing LDAP connection to {server_uri}")
        
        try:
            # Initialize connection
            conn = ldap.initialize(server_uri)
            
            # Set connection options
            for opt, value in conn_options.items():
                conn.set_option(opt, value)
            
            # Try to bind with service account
            self.stdout.write("Binding with service account...")
            conn.simple_bind_s(bind_dn, bind_password)
            self.stdout.write(self.style.SUCCESS("Bind successful!"))
            
            # Search for the user
            search_base = "DC=creditfoncier,DC=cm"
            search_filter = f"(sAMAccountName={username})"
            
            self.stdout.write(f"Searching for user: {username}")
            self.stdout.write(f"Search filter: {search_filter}")
            self.stdout.write(f"Search base: {search_base}")
            
            results = conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter, ['dn', 'mail', 'givenName', 'sn'])
            
            if not results:
                self.stdout.write(self.style.ERROR(f"User {username} not found in LDAP"))
                return
                
            self.stdout.write(self.style.SUCCESS(f"Found {len(results)} results"))
            
            # Display the user's DN and attributes
            for dn, attrs in results:
                self.stdout.write(f"User DN: {dn}")
                for attr, values in attrs.items():
                    for val in values:
                        try:
                            self.stdout.write(f"  {attr}: {val.decode('utf-8')}")
                        except UnicodeDecodeError:
                            self.stdout.write(f"  {attr}: <binary data>")
                            
            # Check if we can bind as this user (would require testing password)
            # This part is commented out since we don't have the user's password
            # user_dn = results[0][0]
            # self.stdout.write(f"Testing bind as user: {user_dn}")
            # conn.simple_bind_s(user_dn, "user_password_here")
            # self.stdout.write(self.style.SUCCESS("User bind successful!"))
            
        except ldap.INVALID_CREDENTIALS:
            self.stdout.write(self.style.ERROR("Invalid service account credentials"))
        except ldap.SERVER_DOWN:
            self.stdout.write(self.style.ERROR("LDAP server is down or unreachable"))
        except ldap.LDAPError as e:
            self.stdout.write(self.style.ERROR(f"LDAP error: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
        finally:
            try:
                conn.unbind_s()
                self.stdout.write("Connection closed")
            except:
                pass