class AuditLogMiddleware:
    """Ghi log nhẹ cho các request thay đổi dữ liệu (POST/PUT/PATCH/DELETE)
    của người dùng đã đăng nhập. Việc ghi log chi tiết theo từng đối tượng
    được thực hiện tại view/service layer (xem core/services.py); middleware
    này chỉ đảm bảo có một điểm log request-level thống nhất, tránh N+1
    log call rải rác."""

    LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if (request.method in self.LOGGED_METHODS
                    and getattr(request, "user", None)
                    and request.user.is_authenticated
                    and response.status_code < 400
                    and not request.path.startswith("/static")
                    and not request.path.startswith("/media")):
                from core.models import AuditLog
                AuditLog.objects.create(
                    user=request.user,
                    action=f"{request.method} {request.path}",
                    path=request.path,
                    method=request.method,
                    ip_address=self._get_ip(request),
                )
        except Exception:
            # Không để lỗi log làm gãy request chính
            pass
        return response

    @staticmethod
    def _get_ip(request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
