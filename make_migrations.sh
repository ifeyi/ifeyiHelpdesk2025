echo "===== Creating migrations for all apps ====="

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

echo "Creating migrations for any remaining apps..."
docker-compose exec django python helpdesk_app/manage.py makemigrations

echo "===== All migrations created ====="

echo "Applying migrations in the correct order..."

echo "Applying contenttypes migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate contenttypes

echo "Applying auth migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate auth

echo "Applying accounts migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate accounts

echo "Applying sites migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate sites

echo "Applying tickets migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate tickets

echo "Applying articles migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate articles

echo "Applying comments migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate comments

echo "Applying core migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate core

echo "Applying remaining migrations..."
docker-compose exec django python helpdesk_app/manage.py migrate

echo "===== All migrations applied ====="