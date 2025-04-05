from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tickets.models import Ticket, Category

User = get_user_model()

class TicketViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create users
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
        
        # Create some tickets
        cls.ticket1 = Ticket.objects.create(
            title='Test Ticket 1',
            description='This is test ticket 1',
            status=Ticket.Status.NEW,
            branch=Ticket.Branch.SIEGE,
            priority=Ticket.Priority.MEDIUM,
            created_by=cls.customer,
            assigned_to=None,
            category=cls.category
        )
        
        cls.ticket2 = Ticket.objects.create(
            title='Test Ticket 2',
            description='This is test ticket 2',
            status=Ticket.Status.IN_PROGRESS,
            branch=Ticket.Branch.SIEGE,
            priority=Ticket.Priority.HIGH,
            created_by=cls.customer,
            assigned_to=cls.agent,
            category=cls.category
        )
    
    def setUp(self):
        self.client = Client()
    
    def test_ticket_list_view_unauthenticated(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(reverse('ticket-list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_ticket_list_view_customer(self):
        """Test that customers can see their own tickets"""
        self.client.login(username='testcustomer', password='password123')
        response = self.client.get(reverse('ticket-list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that the customer sees only their tickets
        tickets = response.context.get('tickets', [])
        self.assertEqual(len(tickets), 2)
        self.assertIn(self.ticket1, tickets)
        self.assertIn(self.ticket2, tickets)
    
    def test_ticket_list_view_agent(self):
        """Test that agents can see all tickets"""
        self.client.login(username='testagent', password='password123')
        response = self.client.get(reverse('ticket-list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that the agent sees all tickets
        tickets = response.context.get('tickets', [])
        self.assertEqual(len(tickets), 2)
        self.assertIn(self.ticket1, tickets)
        self.assertIn(self.ticket2, tickets)
    
    def test_ticket_detail_view(self):
        """Test the ticket detail view"""
        self.client.login(username='testcustomer', password='password123')
        response = self.client.get(reverse('ticket-detail', args=[self.ticket1.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct ticket is shown
        ticket = response.context.get('ticket')
        self.assertEqual(ticket, self.ticket1)
    
    def test_ticket_create_view(self):
        """Test creating a new ticket"""
        self.client.login(username='testcustomer', password='password123')
        
        # GET request should show the form
        response = self.client.get(reverse('ticket-create'))
        self.assertEqual(response.status_code, 200)
        
        # POST request should create a new ticket
        data = {
            'title': 'New Test Ticket',
            'description': 'This is a new test ticket',
            'branch': Ticket.Branch.SIEGE,
            'priority': Ticket.Priority.LOW,
            'category': self.category.pk,
        }
        response = self.client.post(reverse('ticket-create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check that the ticket was created
        self.assertTrue(Ticket.objects.filter(title='New Test Ticket').exists())