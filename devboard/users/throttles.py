from rest_framework.throttling import AnonRateThrottle

class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'

class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'