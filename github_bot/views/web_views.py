"""
Web views for rendering HTML templates.
"""
from django.shortcuts import render


def chat_view(request):
    """
    Render the main chat interface.
    """
    return render(request, 'github_bot/chat.html')


def code_review_view(request):
    """
    Render the code review interface.
    """
    return render(request, 'github_bot/code_review.html')

