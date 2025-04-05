#!/bin/bash

# Create initial migrations for all apps

echo "===== Creating migrations for all apps ====="

# Create migrations for each app
echo "Creating migrations for accounts app..."
docker-compose exec django python helpdesk_app/manage.py makemigrations accounts

echo "Creating migrations for tickets app..."
docker-compose exec django python helpdesk_app/manage.py makemigrations tickets

echo "Creating migrations for articles app..."
docker-compose exec django python helpdesk_app/manage.py makemigrations articles

echo "Creating migrations for comments app..."
docker-compose exec django python helpdesk_app/manage.py makemigrations comments

echo "Creating migrations for core app..."
docker-compose exec django python helpdesk_app/manage.py makemigrations core

# Create migrations for any remaining apps
echo "Creating migrations for any remaining apps..."
docker-compose exec django python helpdesk_app/manage.py makemigrations

echo "===== All migrations created ====="

# Now apply the migrations in the correct order
echo "Applying migrations in the correct order..."

# First, apply only the auth and contenttypes migrations
echo "Applying contenttypes migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate contenttypes

echo "Applying auth migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate auth

# Next, apply the accounts app migrations to create the custom user model
echo "Applying accounts migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate accounts

# Now apply the sites migrations (needed for allauth)
echo "Applying sites migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate sites

# Apply the remaining app migrations one by one
echo "Applying tickets migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate tickets

echo "Applying articles migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate articles

echo "Applying comments migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate comments

echo "Applying core migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate core

# Apply any remaining migrations
echo "Applying remaining migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate

echo "===== All migrations applied ====="