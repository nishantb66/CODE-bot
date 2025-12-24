"""JWT Debugger web URL configuration."""
from django.urls import path
from .web_views import debugger_view

app_name = 'jwt_debugger'

urlpatterns = [
    path('', debugger_view, name='debugger'),
]
