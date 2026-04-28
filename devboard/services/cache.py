from django.core.cache import cache

def invalidate_dashboard_cache(user_id: int) -> None:
    """Clear the dashboard cache for a specific user."""
    cache.delete(f"dashboard:user:{user_id}")