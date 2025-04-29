echo "===== Setting up the Helpdesk Application ====="

echo "Applying migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate

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
echo "Seeding the database with sample data..."
docker-compose exec django python helpdesk_app/manage.py seed_data --tickets 20 --articles 10

echo "Translating..."
docker-compose exec django python helpdesk_app/manage.py makemessages -l fr
docker-compose exec django python helpdesk_app/manage.py makemessages -l en

docker-compose exec django python helpdesk_app/manage.py compilemessages

echo "Collecting static files..."
docker-compose exec django python helpdesk_app/manage.py collectstatic --noinput

echo "Running tests..."
docker-compose exec django python helpdesk_app/manage.py test

echo "===== Setup Complete ====="
echo "You can now access the helpdesk application at http://localhost"
echo "Admin interface: http://localhost/admin"
echo "Admin credentials: ifeyibatindek@gmail.com / B1t9n45K"