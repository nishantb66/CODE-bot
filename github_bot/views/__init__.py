"""
View modules for GitHub Bot API endpoints and web views.

This module provides clean exports for all view classes and functions.
"""

# Chat views
from github_bot.views.chat_views import ChatAPIView
from github_bot.views.chat_stream_views import ChatStreamView

# Code review views
from github_bot.views.code_review_views import (
    CodeReviewAPIView,
    FileReviewAPIView,
    ImprovementSuggestionsAPIView,
)

# Report views
from github_bot.views.report_views import (
    generate_report,
    download_report,
)

# Web views
from github_bot.views.web_views import (
    chat_view,
    code_review_view,
)

__all__ = [
    # Chat
    'ChatAPIView',
    'ChatStreamView',
    # Code Review
    'CodeReviewAPIView',
    'FileReviewAPIView',
    'ImprovementSuggestionsAPIView',
    # Reports
    'generate_report',
    'download_report',
    # Web
    'chat_view',
    'code_review_view',
]
