import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_frontend.settings_railway")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()