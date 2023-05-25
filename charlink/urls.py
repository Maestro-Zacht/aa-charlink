from django.urls import path

from . import views

app_name = 'charlink'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('audit/', views.audit, name='audit'),
    path('audit/corp/<int:corp_id>/', views.audit, name='audit_corp'),
    path('audit/user/<int:user_id>/', views.audit_user, name='audit_user'),
    path('audit/app/<str:app>/', views.audit_app, name='audit_app'),
    path('search/', views.search, name='search'),
]
