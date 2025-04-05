from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import AgentProfile, CustomerProfile
from tickets.models import Category

User = get_user_model()

class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create users of different types
        cls.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            user_type=User.UserType.ADMIN
        )
        
        cls.agent_user = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='password123',
            first_name='Agent',
            last_name='User',
            user_type=User.UserType.AGENT,
            department='Support'
        )
        
        cls.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            first_name='Customer',
            last_name='User',
            user_type=User.UserType.CUSTOMER
        )
    
    def test_user_creation(self):
        """Test creating users with different types"""
        self.assertEqual(str(self.admin_user), 'admin@example.com')
        self.assertEqual(self.admin_user.get_full_name(), 'Admin User')
        self.assertEqual(self.admin_user.user_type, User.UserType.ADMIN)
        
        self.assertEqual(str(self.agent_user), 'agent@example.com')
        self.assertEqual(self.agent_user.department, 'Support')
        self.assertEqual(self.agent_user.user_type, User.UserType.AGENT)
        
        self.assertEqual(str(self.customer_user), 'customer@example.com')
        self.assertEqual(self.customer_user.user_type, User.UserType.CUSTOMER)
    
    def test_user_type_properties(self):
        """Test the user type property methods"""
        self.assertTrue(self.admin_user.is_admin)
        self.assertFalse(self.admin_user.is_agent)
        self.assertFalse(self.admin_user.is_customer)
        
        self.assertFalse(self.agent_user.is_admin)
        self.assertTrue(self.agent_user.is_agent)
        self.assertFalse(self.agent_user.is_customer)
        
        self.assertFalse(self.customer_user.is_admin)
        self.assertFalse(self.customer_user.is_agent)
        self.assertTrue(self.customer_user.is_customer)


class AgentProfileModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an agent user
        cls.agent_user = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='password123',
            user_type=User.UserType.AGENT
        )
        
        # Create some expertise categories
        cls.category1 = Category.objects.create(name='Technical Support')
        cls.category2 = Category.objects.create(name='Billing')
        
        # Create agent profile
        cls.agent_profile = AgentProfile.objects.create(
            user=cls.agent_user,
            bio='Experienced support agent',
            availability_status=True,
            max_tickets=25
        )
        
        # Add expertise
        cls.agent_profile.expertise.add(cls.category1, cls.category2)
    
    def test_agent_profile_creation(self):
        """Test creating an agent profile"""
        self.assertEqual(str(cls.agent_profile), 'Agent: agent@example.com')
        self.assertEqual(cls.agent_profile.user, cls.agent_user)
        self.assertEqual(cls.agent_profile.bio, 'Experienced support agent')
        self.assertTrue(cls.agent_profile.availability_status)
        self.assertEqual(cls.agent_profile.max_tickets, 25)
    
    def test_agent_expertise(self):
        """Test agent expertise categories"""
        self.assertEqual(cls.agent_profile.expertise.count(), 2)
        self.assertIn(cls.category1, cls.agent_profile.expertise.all())
        self.assertIn(cls.category2, cls.agent_profile.expertise.all())


class CustomerProfileModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a customer user
        cls.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            user_type=User.UserType.CUSTOMER
        )
        
        # Create customer profile
        cls.customer_profile = CustomerProfile.objects.create(
            user=cls.customer_user,
            company='Acme Inc.',
            account_id='ACC-12345',
            support_level='Premium'
        )
    
    def test_customer_profile_creation(self):
        """Test creating a customer profile"""
        self.assertEqual(str(cls.customer_profile), 'Customer: customer@example.com')
        self.assertEqual(cls.customer_profile.user, cls.customer_user)
        self.assertEqual(cls.customer_profile.company, 'Acme Inc.')
        self.assertEqual(cls.customer_profile.account_id, 'ACC-12345')
        self.assertEqual(cls.customer_profile.support_level, 'Premium')