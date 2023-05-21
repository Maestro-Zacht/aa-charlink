from django.urls import path

from . import views

app_name = 'charlink'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('audit/', views.audit, name='audit'),
    path('audit/<int:corp_id>/', views.audit, name='audit_corp'),
    path('search/', views.search, name='search'),
]
