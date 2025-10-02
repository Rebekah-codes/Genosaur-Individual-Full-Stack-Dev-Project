from . import views
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('hatch/<int:egg_id>/', views.hatch_egg, name='hatch_egg'),
    path('dinosaur/<int:dino_id>/', views.dinosaur_detail, name='dinosaur_detail'),
    path('dinosaur/<int:dino_id>/action/', views.perform_action, name='perform_action'),
]
