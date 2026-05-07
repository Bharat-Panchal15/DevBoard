import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from users.models import User
from projects.models import Project
from tasks.models import Task

logger = logging.getLogger("api.email")

def _send(*, subject: str, text: str, html: str, to: str) -> None:
    """Base email sender"""
    email = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    email.attach_alternative(html, "text/html")
    email.send()
    logger.info("Email sent successfully", extra={"to": to, "subject": subject})

def send_welcome_email(user: User) -> None:
    _send(
        subject="Welcome to DevBoard!",
        text=f"Welcome, {user.username}! your account has been created successfully.",
        html=f"<h2>Welcome, {user.username}!</h2><p>Your DevBoard account has been created successfully.</p>",
        to=user.email,
    )

def send_member_added_email(new_member: User, project: Project):
    _send(
        subject=f"You've been added to {project.name}",
        text=f"Hi {new_member.username}, you've been added to the project '{project.name}'.",
        html=f"<h2>New Project!</h2><p>You've been added to <strong>{project.name}</strong>.</p>",
        to=new_member.email,
    )

def send_task_assigned_email(assignee: User, task: Task):
    _send(
        subject=f"Task assigned: {task.title}",
        text=f"Hi {assignee.username}, you've been assigned the task '{task.title}'.",
        html=f"<h2>New Task!</h2><p>You've been assigned: <strong>{task.title}</strong>.</p>",
        to=assignee.email,
    )

def send_otp_email(user: User, code: str) -> None:
    _send(
        subject="Your DevBoard verification code",
        text=f"Your OTP is {code}. Valid for 10 minutes.",
        html=f"<h2>Verify your email!</h2><p>Your OTP is <strong>{code}</strong>. Valid for 10 minutes</p>",
        to=user.email,
    )