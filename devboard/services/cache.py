from django.core.cache import cache

def invalidate_dashboard_cache(user_id: int) -> None:
    """Clear the dashboard cache for a specific user."""
    cache.delete(f"dashboard:user:{user_id}")

def invalidate_project_list_cache(user_id: int) -> None:
    """Clear the project list for a specific user."""
    cache.delete(f"projects:user:{user_id}")

def invalidate_event_list_cache(project_id: int) -> None:
    """Clear the even list for a specific user."""
    cache.delete(f"events:user:{project_id}")