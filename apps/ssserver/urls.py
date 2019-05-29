from django.urls import path
from . import views


app_name = "ssserver"
urlpatterns = [path("user/edit/<int:user_id>/", views.user_edit, name="user_edit")]
