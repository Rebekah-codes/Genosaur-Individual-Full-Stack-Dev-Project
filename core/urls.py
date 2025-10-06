from . import views
from django.urls import path

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('hatch/<int:egg_id>/', views.hatch_egg, name='hatch_egg'),
    path('dinosaur/<int:dino_id>/', views.dinosaur_detail, name='dinosaur_detail'),
    path('dinosaur/<int:dino_id>/action/', views.perform_action, name='perform_action'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('claim-egg/', views.claim_egg, name='claim_egg'),
    path('active-nests/', views.active_nests, name='active_nests'),
    path('egg/<int:egg_id>/', views.egg_detail, name='egg_detail'),
    path('hatching/<int:egg_id>/', views.hatching_page, name='hatching_page'),
]
