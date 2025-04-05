from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from tickets.models import Ticket, Category, Tag, SLA

User = get_user_model()

class TicketModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a test user
        cls.customer = User.objects.create_user(
            username='testcustomer',
            email='customer@example.com',
            password='password123',
            user_type='customer'
        )
        
        cls.agent = User.objects.create_user(
            username='testagent',
            email='agent@example.com',
            password='password123',
            user_type='agent'
        )
        
        # Create a category
        cls.category = Category.objects.create(
            name='Test Category',
            description='A test category'
        )
        
        # Create a tag
        cls.tag = Tag.objects.create(name='test-tag')
        
        # Create a ticket
        cls.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='This is a test ticket',
            status=Ticket.Status.NEW,
            branch=Ticket.Branch.SIEGE,
            priority=Ticket.Priority.MEDIUM,
            created_by=cls.customer,
            assigned_to=cls.agent,
            category=cls.category
        )
        cls.ticket.tags.add(cls.tag)
    
    def test_ticket_creation(self):
        """Test the ticket creation"""
        self.assertEqual(str(self.ticket), 'Test Ticket')
        self.assertEqual(self.ticket.status, Ticket.Status.NEW)
        self.assertEqual(self.ticket.branch, Ticket.Branch.SIEGE)
        self.assertEqual(self.ticket.priority, Ticket.Priority.MEDIUM)
        self.assertEqual(self.ticket.created_by, self.customer)
        self.assertEqual(self.ticket.assigned_to, self.agent)
        self.assertEqual(self.ticket.category, self.category)
        self.assertEqual(self.ticket.tags.count(), 1)
        self.assertEqual(self.ticket.tags.first(), self.tag)
    
    def test_ticket_status_transition(self):
        """Test changing ticket status"""
        # Change to in progress
        self.ticket.status = Ticket.Status.IN_PROGRESS
        self.ticket.save()
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)
        
        # Change to resolved
        self.ticket.status = Ticket.Status.RESOLVED
        self.ticket.save()
        self.assertEqual(self.ticket.status, Ticket.Status.RESOLVED)
        
        # Check that the ticket can be closed
        self.assertTrue(self.ticket.can_be_closed())
    
    def test_is_overdue(self):
        """Test the is_overdue property"""
        # Ticket with no due date should not be overdue
        self.assertFalse(self.ticket.is_overdue)
        
        # Set a due date in the past
        self.ticket.due_date = timezone.now() - timezone.timedelta(days=1)
        self.ticket.save()
        self.assertTrue(self.ticket.is_overdue)
        
        # Set a due date in the future
        self.ticket.due_date = timezone.now() + timezone.timedelta(days=1)
        self.ticket.save()
        self.assertFalse(self.ticket.is_overdue)


class CategoryModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a parent category
        cls.parent_category = Category.objects.create(
            name='Parent Category',
            description='A parent category'
        )
        
        # Create a child category
        cls.child_category = Category.objects.create(
            name='Child Category',
            description='A child category',
            parent=cls.parent_category
        )
    
    def test_category_creation(self):
        """Test the category creation"""
        self.assertEqual(str(self.parent_category), 'Parent Category')
        self.assertEqual(str(self.child_category), 'Child Category')
    
    def test_category_hierarchy(self):
        """Test the category parent-child relationship"""
        self.assertEqual(self.child_category.parent, self.parent_category)
        self.assertEqual(self.parent_category.subcategories.count(), 1)
        self.assertEqual(self.parent_category.subcategories.first(), self.child_category)


class SLAModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an SLA
        cls.sla = SLA.objects.create(
            name='Test SLA',
            description='A test SLA',
            response_time_low=24,
            response_time_medium=12,
            response_time_high=4,
            response_time_critical=1,
            resolution_time_low=72,
            resolution_time_medium=48,
            resolution_time_high=24,
            resolution_time_critical=8,
            business_hours_only=True
        )
    
    def test_sla_creation(self):
        """Test the SLA creation"""
        self.assertEqual(str(self.sla), 'Test SLA')
        self.assertEqual(self.sla.response_time_low, 24)
        self.assertEqual(self.sla.resolution_time_critical, 8)
        self.assertTrue(self.sla.business_hours_only)
    
    def test_get_response_time(self):
        """Test the get_response_time method"""
        self.assertEqual(self.sla.get_response_time(Ticket.Priority.LOW), 24)
        self.assertEqual(self.sla.get_response_time(Ticket.Priority.MEDIUM), 12)
        self.assertEqual(self.sla.get_response_time(Ticket.Priority.HIGH), 4)
        self.assertEqual(self.sla.get_response_time(Ticket.Priority.CRITICAL), 1)
    
    def test_get_resolution_time(self):
        """Test the get_resolution_time method"""
        self.assertEqual(self.sla.get_resolution_time(Ticket.Priority.LOW), 72)
        self.assertEqual(self.sla.get_resolution_time(Ticket.Priority.MEDIUM), 48)
        self.assertEqual(self.sla.get_resolution_time(Ticket.Priority.HIGH), 24)
        self.assertEqual(self.sla.get_resolution_time(Ticket.Priority.CRITICAL), 8)