# app/email_tasks.py

from app.celery_app import celery


@celery.task
def send_reminder_email(to: str, subject: str, body: str):
    # placeholder—prints to your worker’s console
    print(f"[REMINDER EMAIL] To: {to}\nSubject: {subject}\n\n{body}")
