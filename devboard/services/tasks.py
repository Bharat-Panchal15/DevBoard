from celery import shared_task

@shared_task
def send_welcome_email_task(user_id: int) -> None:
    from users.models import User
    from services.email import send_welcome_email

    user = User.objects.get(id=user_id)
    send_welcome_email(user)

@shared_task
def send_member_added_email_task(user_id: int, project_id: int) -> None:
    from users.models import User
    from projects.models import Project
    from services.email import send_member_added_email

    user = User.objects.get(id=user_id)
    project = Project.objects.get(id=project_id)
    send_member_added_email(user, project)

@shared_task
def send_task_assigned_email_task(user_id: int, task_id: int) -> None:
    from users.models import User
    from tasks.models import Task
    from services.email import send_task_assigned_email

    user = User.objects.get(id=user_id)
    task = Task.objects.get(id=task_id)
    send_task_assigned_email(user, task)