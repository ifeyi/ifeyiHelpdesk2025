from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from tickets.models import Ticket, Category, Tag, SLA
from articles.models import Article, ArticleCategory, ArticleTag
from accounts.models import AgentProfile, CustomerProfile
from comments.models import Comment
from django.contrib.contenttypes.models import ContentType

import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with sample data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tickets',
            default=20,
            type=int,
            help='Number of tickets to create'
        )
        parser.add_argument(
            '--articles',
            default=10,
            type=int,
            help='Number of articles to create'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding database...'))
        
        # Create users of different types
        self.create_users()
        
        # Create ticket categories and tags
        categories = self.create_ticket_categories()
        tags = self.create_tags()
        
        # Create SLA profiles
        slas = self.create_slas()
        
        # Create knowledge base categories
        article_categories = self.create_article_categories()
        article_tags = self.create_article_tags()
        
        # Create tickets
        tickets = self.create_tickets(options['tickets'], categories, tags)
        
        # Create articles
        articles = self.create_articles(options['articles'], article_categories, article_tags)
        
        # Create comments for tickets and articles
        self.create_comments(tickets, articles)
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    def create_users(self):
        self.stdout.write('Creating users...')
        
        # Ensure an admin user exists
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                user_type=User.UserType.ADMIN
            )
            self.stdout.write(f'Admin user created: {admin.email}')
        
        # Create agent users
        agent_data = [
            {'username': 'agent1', 'email': 'agent1@example.com', 'first_name': 'John', 'last_name': 'Smith', 'department': 'Technical Support'},
            {'username': 'agent2', 'email': 'agent2@example.com', 'first_name': 'Jane', 'last_name': 'Doe', 'department': 'Customer Success'},
            {'username': 'agent3', 'email': 'agent3@example.com', 'first_name': 'Michael', 'last_name': 'Johnson', 'department': 'Technical Support'},
        ]
        
        for data in agent_data:
            if not User.objects.filter(username=data['username']).exists():
                agent = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password='password123',
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    user_type=User.UserType.AGENT,
                    department=data['department']
                )
                
                # Create agent profile
                AgentProfile.objects.get_or_create(
                    user=agent,
                    defaults={
                        'bio': f'Support agent specializing in {data["department"]}',
                        'availability_status': True,
                        'max_tickets': 20
                    }
                )
                self.stdout.write(f'Agent created: {agent.email}')
        
        # Create customer users
        customer_data = [
            {'username': 'customer1', 'email': 'customer1@example.com', 'first_name': 'Sarah', 'last_name': 'Parker', 'company': 'Acme Inc.'},
            {'username': 'customer2', 'email': 'customer2@example.com', 'first_name': 'Robert', 'last_name': 'Wilson', 'company': 'Example Corp'},
            {'username': 'customer3', 'email': 'customer3@example.com', 'first_name': 'Emily', 'last_name': 'Brown', 'company': 'Test LLC'},
            {'username': 'customer4', 'email': 'customer4@example.com', 'first_name': 'David', 'last_name': 'Miller', 'company': 'Sample Co.'},
            {'username': 'customer5', 'email': 'customer5@example.com', 'first_name': 'Lisa', 'last_name': 'Taylor', 'company': 'Demo Industries'},
        ]
        
        for data in customer_data:
            if not User.objects.filter(username=data['username']).exists():
                customer = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password='password123',
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    user_type=User.UserType.CUSTOMER
                )
                
                # Create customer profile
                CustomerProfile.objects.get_or_create(
                    user=customer,
                    defaults={
                        'company': data['company'],
                        'account_id': f'ACC-{random.randint(10000, 99999)}',
                        'support_level': random.choice(['Basic', 'Standard', 'Premium'])
                    }
                )
                self.stdout.write(f'Customer created: {customer.email}')

    def create_ticket_categories(self):
        self.stdout.write('Creating ticket categories...')
        
        categories = []
        
        # Main categories
        technical = Category.objects.get_or_create(
            name='Technical Support',
            defaults={'description': 'Technical issues and troubleshooting'}
        )[0]
        categories.append(technical)
        
        billing = Category.objects.get_or_create(
            name='Billing',
            defaults={'description': 'Billing and payment related queries'}
        )[0]
        categories.append(billing)
        
        feature = Category.objects.get_or_create(
            name='Feature Request',
            defaults={'description': 'Requests for new features or enhancements'}
        )[0]
        categories.append(feature)
        
        account = Category.objects.get_or_create(
            name='Account',
            defaults={'description': 'Account management queries'}
        )[0]
        categories.append(account)
        
        # Subcategories
        Category.objects.get_or_create(
            name='Login Issues',
            defaults={'description': 'Problems with logging in', 'parent': technical}
        )
        
        Category.objects.get_or_create(
            name='Performance',
            defaults={'description': 'Performance related issues', 'parent': technical}
        )
        
        Category.objects.get_or_create(
            name='Payment Failed',
            defaults={'description': 'Issues with payment processing', 'parent': billing}
        )
        
        Category.objects.get_or_create(
            name='Refund Request',
            defaults={'description': 'Requests for refunds', 'parent': billing}
        )
        
        return categories

    def create_tags(self):
        self.stdout.write('Creating tags...')
        
        tags = []
        tag_names = ['urgent', 'bug', 'enhancement', 'easy-fix', 'needs-info', 'customer-priority', 'waiting-approval']
        
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
            if created:
                self.stdout.write(f'Created tag: {name}')
        
        return tags

    def create_slas(self):
        self.stdout.write('Creating SLAs...')
        
        slas = []
        
        standard, created = SLA.objects.get_or_create(
            name='Standard',
            defaults={
                'description': 'Standard service level agreement',
                'response_time_low': 24,
                'response_time_medium': 12,
                'response_time_high': 4,
                'response_time_critical': 1,
                'resolution_time_low': 72,
                'resolution_time_medium': 48,
                'resolution_time_high': 24,
                'resolution_time_critical': 8,
                'business_hours_only': True
            }
        )
        slas.append(standard)
        if created:
            self.stdout.write(f'Created SLA: {standard.name}')
        
        premium, created = SLA.objects.get_or_create(
            name='Premium',
            defaults={
                'description': 'Premium service level agreement',
                'response_time_low': 12,
                'response_time_medium': 6,
                'response_time_high': 2,
                'response_time_critical': 1,
                'resolution_time_low': 48,
                'resolution_time_medium': 24,
                'resolution_time_high': 12,
                'resolution_time_critical': 4,
                'business_hours_only': False
            }
        )
        slas.append(premium)
        if created:
            self.stdout.write(f'Created SLA: {premium.name}')
        
        return slas

    def create_article_categories(self):
        self.stdout.write('Creating article categories...')
        
        categories = []
        
        # Main categories
        getting_started = ArticleCategory.objects.get_or_create(
            name='Getting Started',
            slug='getting-started',
            defaults={'description': 'Guides to help you get started with our products'}
        )[0]
        categories.append(getting_started)
        
        troubleshooting = ArticleCategory.objects.get_or_create(
            name='Troubleshooting',
            slug='troubleshooting',
            defaults={'description': 'Solutions for common problems'}
        )[0]
        categories.append(troubleshooting)
        
        faqs = ArticleCategory.objects.get_or_create(
            name='FAQ',
            slug='faq',
            defaults={'description': 'Frequently asked questions'}
        )[0]
        categories.append(faqs)
        
        # Subcategories
        ArticleCategory.objects.get_or_create(
            name='Installation',
            slug='installation',
            defaults={'description': 'Installation guides', 'parent': getting_started}
        )
        
        ArticleCategory.objects.get_or_create(
            name='Configuration',
            slug='configuration',
            defaults={'description': 'Configuration guides', 'parent': getting_started}
        )
        
        ArticleCategory.objects.get_or_create(
            name='Common Errors',
            slug='common-errors',
            defaults={'description': 'Solutions for common errors', 'parent': troubleshooting}
        )
        
        return categories

    def create_article_tags(self):
        self.stdout.write('Creating article tags...')
        
        tags = []
        tag_data = [
            {'name': 'Beginner', 'slug': 'beginner'},
            {'name': 'Advanced', 'slug': 'advanced'},
            {'name': 'Tutorial', 'slug': 'tutorial'},
            {'name': 'How-to', 'slug': 'how-to'},
            {'name': 'Reference', 'slug': 'reference'},
            {'name': 'Best Practice', 'slug': 'best-practice'},
        ]
        
        for data in tag_data:
            tag, created = ArticleTag.objects.get_or_create(
                name=data['name'],
                slug=data['slug']
            )
            tags.append(tag)
            if created:
                self.stdout.write(f'Created article tag: {tag.name}')
        
        return tags

    def create_tickets(self, count, categories, tags):
        self.stdout.write(f'Creating {count} tickets...')
        
        tickets = []
        
        # Get customers and agents
        customers = User.objects.filter(user_type=User.UserType.CUSTOMER)
        agents = User.objects.filter(user_type=User.UserType.AGENT)
        
        if not customers or not agents:
            self.stdout.write(self.style.WARNING('Cannot create tickets: need customers and agents'))
            return tickets
        
        statuses = list(Ticket.Status)
        priorities = list(Ticket.Priority)
        
        for i in range(count):
            customer = random.choice(customers)
            agent = random.choice(agents) if random.random() < 0.8 else None  # 20% of tickets unassigned
            category = random.choice(categories)
            status = random.choice(statuses)
            priority = random.choice(priorities)
            
            # Create ticket
            ticket = Ticket.objects.create(
                title=f'Sample Ticket #{i+1}: {category.name} Issue',
                description=f'This is a sample ticket for {category.name}. It has {priority} priority and is {status} status.',
                status=status,
                priority=priority,
                created_by=customer,
                assigned_to=agent,
                category=category
            )
            
            # Add random tags
            ticket_tags = random.sample(tags, random.randint(0, min(3, len(tags))))
            ticket.tags.add(*ticket_tags)
            
            tickets.append(ticket)
            self.stdout.write(f'Created ticket: {ticket.title}')
        
        return tickets

    def create_articles(self, count, categories, tags):
        self.stdout.write(f'Creating {count} articles...')
        
        articles = []
        
        # Get agent users for authorship
        agents = User.objects.filter(user_type=User.UserType.AGENT)
        
        if not agents:
            self.stdout.write(self.style.WARNING('Cannot create articles: need agent users'))
            return articles
        
        statuses = list(Article.Status)
        
        # Sample articles with more realistic content
        article_templates = [
            {
                'title': 'Getting Started with Our Platform',
                'content': '''
# Getting Started with Our Platform

Welcome to our platform! This guide will help you get started with using our services effectively.

## First Steps

1. **Create an account** - Sign up using your email address
2. **Complete your profile** - Add your details and preferences
3. **Explore the dashboard** - Familiarize yourself with the interface

## Key Features

Our platform offers several key features to enhance your experience:

- Real-time analytics
- Customizable dashboards
- Integration with popular tools
- Automated reporting

## Need Help?

If you need assistance at any point, you can:
- Check our [documentation](https://example.com/docs)
- Contact our support team
- Join our community forum

We're excited to have you on board!
                '''
            },
            {
                'title': 'Troubleshooting Common Issues',
                'content': '''
# Troubleshooting Common Issues

This guide addresses the most common issues users encounter and provides solutions.

## Connection Problems

If you're experiencing connection issues:

1. Check your internet connection
2. Verify that our service is operational by checking our status page
3. Clear your browser cache and cookies
4. Try using a different browser or device

## Authentication Errors

Authentication errors typically occur due to:

- Incorrect email or password
- Expired sessions
- Account lockouts after multiple failed attempts

To resolve these issues, try resetting your password or contacting support if the problem persists.

## Performance Issues

If the application is running slowly:

- Check your internet speed
- Close unnecessary browser tabs and applications
- Clear your browser cache
- Update your browser to the latest version

## Still Having Problems?

If you've tried these solutions and are still experiencing issues, please contact our support team with the following information:

- Error messages (screenshots are helpful)
- Steps to reproduce the issue
- Your browser and operating system
                '''
            },
            {
                'title': 'Advanced Configuration Options',
                'content': '''
# Advanced Configuration Options

This guide covers advanced configuration options for power users.

## Custom Workflows

Create custom workflows by:

1. Navigating to Settings > Workflows
2. Clicking "Create New Workflow"
3. Defining triggers and actions
4. Testing and activating your workflow

## API Integration

Our platform offers a robust API for integration with other services:

```
# Example API request
curl -X GET https://api.example.com/v1/resources \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Security Settings

Enhance your account security by:

- Enabling two-factor authentication
- Setting up IP restrictions
- Configuring session timeout limits
- Creating role-based access controls

## Performance Tuning

Optimize performance by:

- Adjusting cache settings
- Configuring batch processing options
- Scheduling resource-intensive operations during off-peak hours

These advanced options allow you to customize the platform to your specific needs.
                '''
            }
        ]
        
        # Create articles
        for i in range(count):
            # Use template if available, otherwise generate generic content
            if i < len(article_templates):
                title = article_templates[i]['title']
                content = article_templates[i]['content']
                summary = title
            else:
                title = f'Sample Article #{i+1}'
                content = f'This is the content for sample article #{i+1}. It contains information that users might find helpful.'
                summary = f'Summary for article #{i+1}'
            
            author = random.choice(agents)
            category = random.choice(categories)
            status = random.choice(statuses)
            
            # Create article
            article = Article.objects.create(
                title=title,
                slug=f'article-{i+1}',
                content=content,
                summary=summary,
                status=status,
                author=author,
                is_featured=(random.random() < 0.2),  # 20% chance of being featured
            )
            
            # Add random categories (1-2)
            article_categories = random.sample(categories, random.randint(1, min(2, len(categories))))
            article.categories.add(*article_categories)
            
            # Add random tags
            article_tags = random.sample(tags, random.randint(0, min(3, len(tags))))
            article.tags.add(*article_tags)
            
            # If published, set published date
            if status == Article.Status.PUBLISHED:
                article.published_at = timezone.now() - timedelta(days=random.randint(1, 30))
                article.save()
            
            articles.append(article)
            self.stdout.write(f'Created article: {article.title}')
        
        return articles

    def create_comments(self, tickets, articles):
        self.stdout.write('Creating comments...')
        
        # Get users
        users = User.objects.all()
        
        if not users:
            self.stdout.write(self.style.WARNING('Cannot create comments: need users'))
            return
        
        # Get content types
        ticket_ct = ContentType.objects.get_for_model(Ticket)
        article_ct = ContentType.objects.get_for_model(Article)
        
        # Comments for tickets
        for ticket in tickets:
            # 1-3 comments per ticket
            for _ in range(random.randint(1, 3)):
                user = random.choice(users)
                is_internal = user.user_type != User.UserType.CUSTOMER and random.random() < 0.3  # 30% chance of internal comment for staff
                
                Comment.objects.create(
                    content_type=ticket_ct,
                    object_id=ticket.id,
                    author=user,
                    text=f'This is a {"internal " if is_internal else ""}comment on ticket #{ticket.id}. {" This comment is only visible to staff." if is_internal else ""}',
                    is_internal=is_internal,
                    created_at=timezone.now() - timedelta(days=random.randint(0, 5), hours=random.randint(0, 23))
                )
                
        # Comments for articles
        for article in articles:
            # 0-5 comments per article
            for _ in range(random.randint(0, 5)):
                user = random.choice(users)
                
                Comment.objects.create(
                    content_type=article_ct,
                    object_id=article.id,
                    author=user,
                    text=f'This is a comment on the article "{article.title}". Thanks for the information!',
                    created_at=timezone.now() - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))
                )