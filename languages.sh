# Extract messages from Python code and templates
docker-compose exec django python helpdesk_app/manage.py makemessages -l fr
docker-compose exec django python helpdesk_app/manage.py makemessages -l en

# Compile message files after editing translations
docker-compose exec django python helpdesk_app/manage.py compilemessages


echo "===== Language files created ! ====="