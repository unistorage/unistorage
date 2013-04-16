import newrelic.agent

import settings
from app import create_app


app = create_app()

if not settings.DEBUG and not settings.TESTING:
    try:
        import newrelic.agent
        newrelic.agent.initialize('newrelic.ini')
        app.wsgi_app = newrelic.agent.wsgi_application()(app.wsgi_app)
    except:
        pass
