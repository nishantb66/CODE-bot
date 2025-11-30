from django.urls import path
from github_bot.views.chat_views import ChatAPIView
from github_bot.views.chat_stream_views import ChatStreamView
from github_bot.views.web_views import chat_view, code_review_view
from github_bot.views.code_review_views import (
    CodeReviewAPIView,
    FileReviewAPIView,
    ImprovementSuggestionsAPIView
)

app_name = 'github_bot'

urlpatterns = [
    # Chat endpoints
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('chat/stream/', ChatStreamView.as_view(), name='chat_stream'),
    
    # Code review endpoints
    path('review-code/', CodeReviewAPIView.as_view(), name='review_code'),
    path('review-file/', FileReviewAPIView.as_view(), name='review_file'),
    path('suggest-improvements/', ImprovementSuggestionsAPIView.as_view(), name='suggest_improvements'),
    
    # Web views
    path('code-review/', code_review_view, name='code_review_page'),
    path('', chat_view, name='home'),
]


