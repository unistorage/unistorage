import settings
from app import create_app


create_app().run(debug=settings.DEBUG)
