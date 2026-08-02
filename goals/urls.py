from django.urls import path
from . import views

app_name = "goals"

urlpatterns = [
    path("", views.goal_list_view, name="goal_list"),
    path("them/", views.goal_add_view, name="goal_add"),
    path("<int:pk>/", views.goal_detail_view, name="goal_detail"),
    path("<int:pk>/xoa/", views.goal_delete_view, name="goal_delete"),
]
