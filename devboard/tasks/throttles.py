from rest_framework.throttling import UserRateThrottle

class TaskRateThrottle(UserRateThrottle):
    scope = 'task'

class CommentRateThrottle(UserRateThrottle):
    scope = 'comment'