from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from comments.models import Comment, CommentAttachment
from tickets.models import Ticket
from articles.models import Article

User = get_user_model()

class CommentModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.agent = User.objects.create_user(
            username='agent',
            email='agent@example.com',
            password='password123',
            user_type='agent'
        )
        
        cls.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='password123',
            user_type='customer'
        )
        
        # Create a ticket
        cls.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='This is a test ticket',
            status='new',
            priority='medium',
            created_by=cls.customer
        )
        
        # Create an article
        cls.article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            content='This is a test article',
            status='published',
            author=cls.agent
        )
        
        # Get content types
        cls.ticket_ct = ContentType.objects.get_for_model(Ticket)
        cls.article_ct = ContentType.objects.get_for_model(Article)
        
        # Create comments
        cls.ticket_comment = Comment.objects.create(
            content_type=cls.ticket_ct,
            object_id=cls.ticket.id,
            author=cls.agent,
            text='This is a comment on a ticket',
            is_internal=False
        )
        
        cls.internal_comment = Comment.objects.create(
            content_type=cls.ticket_ct,
            object_id=cls.ticket.id,
            author=cls.agent,
            text='This is an internal comment',
            is_internal=True
        )
        
        cls.article_comment = Comment.objects.create(
            content_type=cls.article_ct,
            object_id=cls.article.id,
            author=cls.customer,
            text='This is a comment on an article',
            is_internal=False
        )
    
    def test_comment_creation(self):
        """Test creating comments"""
        self.assertEqual(str(self.ticket_comment), f"Comment by {self.agent} on {self.ticket}")
        self.assertEqual(str(self.internal_comment), f"Comment by {self.agent} on {self.ticket}")
        self.assertEqual(str(self.article_comment), f"Comment by {self.customer} on {self.article}")
    
    def test_comment_relationships(self):
        """Test the generic relationships of comments"""
        # Check ticket comments
        ticket_comments = Comment.objects.filter(
            content_type=self.ticket_ct,
            object_id=self.ticket.id
        )
        self.assertEqual(ticket_comments.count(), 2)
        
        # Check article comments
        article_comments = Comment.objects.filter(
            content_type=self.article_ct,
            object_id=self.article.id
        )
        self.assertEqual(article_comments.count(), 1)
    
    def test_internal_comments(self):
        """Test the internal flag on comments"""
        self.assertFalse(self.ticket_comment.is_internal)
        self.assertTrue(self.internal_comment.is_internal)
        self.assertFalse(self.article_comment.is_internal)


class CommentAttachmentModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a user
        cls.user = User.objects.create_user(
            username='testuser',
            email='user@example.com',
            password='password123'
        )
        
        # Create a ticket
        cls.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='This is a test ticket',
            status='new',
            priority='medium',
            created_by=cls.user
        )
        
        # Get content type
        cls.ticket_ct = ContentType.objects.get_for_model(Ticket)
        
        # Create a comment
        cls.comment = Comment.objects.create(
            content_type=cls.ticket_ct,
            object_id=cls.ticket.id,
            author=cls.user,
            text='This is a comment with an attachment'
        )
        
        # Create a comment attachment (without an actual file)
        cls.attachment = CommentAttachment.objects.create(
            comment=cls.comment,
            description='Test attachment'
        )
    
    def test_attachment_creation(self):
        """Test creating a comment attachment"""
        self.assertEqual(str(self.attachment), f"Attachment for {self.comment}")
        self.assertEqual(self.attachment.comment, self.comment)
        self.assertEqual(self.attachment.description, 'Test attachment')