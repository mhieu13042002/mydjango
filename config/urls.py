from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("tai-khoan/", include("accounts.urls")),
    path("ngan-sach/", include("budgets.urls")),
    path("muc-tieu/", include("goals.urls")),
    path("thong-bao/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
else:
    # Whitenoise đã lo static files (CSS/JS) khi DEBUG=False, nhưng KHÔNG lo
    # media (ảnh người dùng upload: avatar, ảnh chi tiêu AI). Cần serve thủ
    # công route này, nếu không ảnh upload sẽ luôn bị 404 trên production.
    # Lưu ý: đây không phải cách tối ưu cho hệ thống lớn (nên dùng S3/Cloudinary
    # + Railway Volume cho dữ liệu lớn), nhưng đủ dùng cho quy mô dự án này.
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
