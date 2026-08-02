def unread_notifications(request):
    if not request.user.is_authenticated:
        return {}
    from notifications.models import Notification
    qs = Notification.objects.filter(user=request.user)
    return {
        "unread_notifications_count": qs.filter(is_read=False).count(),
        "recent_notifications": qs[:6],
    }
