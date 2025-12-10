"""
URL configuration for GitHub Bot API and web views.

Routes are organized into:
- Chat endpoints for AI conversation
- Code review endpoints for code analysis
- Report generation endpoints for PDF reports
- Web views for HTML templates
"""

from django.urls import path
from github_bot.views import (
    # Chat
    ChatAPIView,
    ChatStreamView,
    # Code Review
    CodeReviewAPIView,
    FileReviewAPIView,
    ImprovementSuggestionsAPIView,
    # Reports
    generate_report,
    download_report,
    # Web
    chat_view,
    code_review_view,
)

app_name = 'github_bot'

urlpatterns = [
    # ============================================
    # Chat Endpoints
    # ============================================
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('chat/stream/', ChatStreamView.as_view(), name='chat_stream'),
    
    # ============================================
    # Code Review Endpoints
    # ============================================
    path('review-code/', CodeReviewAPIView.as_view(), name='review_code'),
    path('review-file/', FileReviewAPIView.as_view(), name='review_file'),
    path('suggest-improvements/', ImprovementSuggestionsAPIView.as_view(), name='suggest_improvements'),
    
    # ============================================
    # Report Generation Endpoints
    # ============================================
    path('generate-report/', generate_report, name='generate_report'),
    path('download-report/', download_report, name='download_report'),
    
    # ============================================
    # Web Views (HTML Templates)
    # ============================================
    path('code-review/', code_review_view, name='code_review_page'),
    path('', chat_view, name='home'),
]
