from rest_framework.throttling import UserRateThrottle

class ProjectRateThrottle(UserRateThrottle):
    scope = 'project'

class MemberRateThrottle(UserRateThrottle):
    scope = 'member'