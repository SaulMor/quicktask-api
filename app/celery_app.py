from celery import Celery

# Point at your local Redis broker & backend
celery = Celery(
    "quicktask",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.email_tasks"],
)
