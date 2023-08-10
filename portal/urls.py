from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("portal/index", views.index, name="index"),
    path("portal/home", views.HomeView.as_view(), name="home"),
    path("portal/about", views.about, name="about"),
    path("", views.HomeView.as_view(), name="about-page"),
]
