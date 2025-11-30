"""
DRF serializers for GitHub Bot API.
"""
from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat request."""
    
    prompt = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=5000,
        help_text="User's question or prompt for the GitHub bot"
    )
    
    model_id = serializers.IntegerField(
        required=False,
        default=2,
        help_text="Model ID: 1 = llama-3.1-8b-instant, 2 = llama-3.3-70b-versatile (default: 2)"
    )
    
    conversation_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        help_text="Optional: Conversation ID to maintain chat history. If not provided, a new conversation starts."
    )
    
    clear_history = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Optional: Set to true to clear conversation history for the given conversation_id"
    )
    
    def validate_prompt(self, value):
        """Validate that prompt is not empty after stripping."""
        if not value.strip():
            raise serializers.ValidationError("Prompt cannot be empty or contain only whitespace.")
        return value.strip()
    
    def validate_model_id(self, value):
        """Validate that model_id is a valid option."""
        from github_bot.constants import GROQ_MODELS
        if value not in GROQ_MODELS:
            available_models = ", ".join([f"{k}={v}" for k, v in GROQ_MODELS.items()])
            raise serializers.ValidationError(
                f"Invalid model_id. Available models: {available_models}"
            )
        return value


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat response."""
    
    success = serializers.BooleanField()
    response = serializers.CharField()
    error = serializers.CharField(required=False, allow_null=True)
    conversation_id = serializers.CharField(required=False, allow_null=True)
    metadata = serializers.DictField(required=False, allow_null=True)


class CodeReviewRequestSerializer(serializers.Serializer):
    """Serializer for code review request."""
    
    code = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Code to review"
    )
    
    language = serializers.CharField(
        required=False,
        default="python",
        max_length=50,
        help_text="Programming language (e.g., python, javascript, java)"
    )
    
    context = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Optional context about the code"
    )
    
    model_id = serializers.IntegerField(
        required=False,
        default=2,
        help_text="Model ID to use for review"
    )
    
    def validate_code(self, value):
        """Validate that code is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Code cannot be empty.")
        return value.strip()


class FileReviewRequestSerializer(serializers.Serializer):
    """Serializer for file review request."""
    
    owner = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Repository owner username"
    )
    
    repo = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Repository name"
    )
    
    file_path = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Path to file in repository"
    )
    
    model_id = serializers.IntegerField(
        required=False,
        default=2,
        help_text="Model ID to use for review"
    )


class ImprovementRequestSerializer(serializers.Serializer):
    """Serializer for code improvement suggestions request."""
    
    code = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Code to improve"
    )
    
    language = serializers.CharField(
        required=False,
        default="python",
        max_length=50,
        help_text="Programming language"
    )
    
    focus_areas = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text="Areas to focus on (e.g., performance, readability, security)"
    )
    
    model_id = serializers.IntegerField(
        required=False,
        default=2,
        help_text="Model ID to use"
    )
    
    def validate_code(self, value):
        """Validate that code is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Code cannot be empty.")
        return value.strip()


class CodeReviewResponseSerializer(serializers.Serializer):
    """Serializer for code review response."""
    
    success = serializers.BooleanField()
    review = serializers.DictField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    language = serializers.CharField(required=False, allow_null=True)
    code_length = serializers.IntegerField(required=False, allow_null=True)

