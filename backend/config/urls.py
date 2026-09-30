from django.urls import path
from pipeline import views

urlpatterns = [
    path('api/session/', views.session), path('api/health/', views.health),
    path('api/connections/', views.connect), path('api/connections/<uuid:connection_id>/disconnect/', views.disconnect),
    path('api/jobs/', views.jobs), path('api/jobs/submit/', views.submit),
    path('api/jobs/<uuid:job_id>/', views.detail), path('api/jobs/<uuid:job_id>/result/', views.result),
    path('api/jobs/<uuid:job_id>/cancel/', views.cancel), path('api/metrics/', views.metrics),
]
