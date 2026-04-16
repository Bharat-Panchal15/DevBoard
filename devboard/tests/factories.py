import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from projects.models import Project
from tasks.models import Task, Comment

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "password123")
        self.save()

class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    
    name = factory.Sequence(lambda n: f"Project {n}")
    description = "Test project description"
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return
        
        self.members.add(self.owner)

        if extracted:
            for member in extracted:
                self.members.add(member)

class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task
    
    title = factory.Sequence(lambda n: f"Task {n}")
    description = "Test Task Description"
    project = factory.SubFactory(ProjectFactory)
    created_by = factory.SubFactory(UserFactory)
    status = Task.StatusChoices.TODO

class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment
    
    content = factory.Sequence(lambda n: F"Comment {n}")
    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)