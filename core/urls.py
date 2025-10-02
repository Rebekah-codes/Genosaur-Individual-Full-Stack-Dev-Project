from . import views
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('hatch/<int:egg_id>/', views.hatch_egg, name='hatch_egg'),
]
