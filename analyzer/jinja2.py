"""
Jinja2 environment configuration for Django.
"""
from jinja2 import Environment
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse


def environment(**options):
    """
    Create and configure Jinja2 environment for Django.
    """
    env = Environment(**options)
    
    # Add Django-specific functions to Jinja2 environment
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    
    return env

