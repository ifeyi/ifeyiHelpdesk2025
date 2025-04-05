#!/bin/bash

# This script sets up the entire helpdesk application
# It applies migrations, seeds data, and runs initial tests

echo "===== Setting up the Helpdesk Application ====="

# Apply migrations
echo "Applying migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate

# Create a superuser for admin access
echo "Creating superuser..."
docker-compose exec -T django python helpdesk_app/manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='ifeyibatindek').exists():
    User.objects.create_superuser('ifeyibatindek', 'ifeyibatindek@gmail.com', 'B1t9n45K')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Seed the database with sample data
echo "Seeding the database with sample data..."
docker-compose exec django python helpdesk_app/manage.py seed_data --tickets 20 --articles 10

# Collect static files
echo "Collecting static files..."
docker-compose exec django python helpdesk_app/manage.py collectstatic --noinput

# Run tests
echo "Running tests..."
docker-compose exec django python helpdesk_app/manage.py test

echo "===== Setup Complete ====="
echo "You can now access the helpdesk application at http://localhost"
echo "Admin interface: http://localhost/admin"
echo "Admin credentials: ifeyibatindek@gmail.com / B1t9n45K"