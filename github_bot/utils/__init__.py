"""
Utility modules for GitHub Bot application.

This module provides clean exports for commonly used utility classes and functions.
"""

# Core services
from github_bot.utils.chat_service import ChatService
from github_bot.utils.github_service import GitHubService
from github_bot.utils.groq_service import GroqService
from github_bot.utils.code_review_service import CodeReviewService
from github_bot.utils.report_generator import EnhancedReportGenerator, generate_repo_report

# Helper utilities
from github_bot.utils.cache import github_cache
from github_bot.utils.database import (
    get_db,
    save_chat_log,
    save_request_log,
    save_error_log,
    save_conversation_message,
    get_conversation_history,
    clear_conversation,
)

__all__ = [
    # Core services
    'ChatService',
    'GitHubService',
    'GroqService',
    'CodeReviewService',
    'EnhancedReportGenerator',
    'generate_repo_report',
    # Cache
    'github_cache',
    # Database utilities
    'get_db',
    'save_chat_log',
    'save_request_log',
    'save_error_log',
    'save_conversation_message',
    'get_conversation_history',
    'clear_conversation',
]
