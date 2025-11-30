"""
Constants and configuration for the GitHub Bot application.
"""

# System instruction prompt for AI assistant
SYSTEM_INSTRUCTION = """You are a helpful GitHub repository assistant. You have access to the user's GitHub repositories and can answer questions about:
- Repository information (name, description, language, stars, forks, etc.)
- Repository code and file contents
- Repository structure and organization
- Commit history and changes
- Issues and pull requests
- Any other questions about the user's GitHub repositories

Always be helpful, accurate, and provide clear explanations. If you don't have access to specific information, let the user know politely.

When discussing repositories, provide relevant details like:
- Repository name and description
- Primary programming language
- Number of stars, forks, and watchers
- Recent activity
- Key files and their purposes

Be conversational and friendly in your responses."""

# GitHub API Configuration
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}

# Groq Model Configuration
# Model mapping: 
# 1 = llama-3.3-70b-versatile (replacement for deprecated llama3-70b-8192)
# 2 = llama-3.3-70b-versatile
GROQ_MODELS = {
    1: "llama-3.1-8b-instant",
    2: "llama-3.3-70b-versatile",
}

# Default model (fallback)
DEFAULT_GROQ_MODEL = 2
GROQ_MODEL = GROQ_MODELS[DEFAULT_GROQ_MODEL]

# MongoDB Collection Names
COLLECTION_CHAT_LOGS = "chat_logs"
COLLECTION_REQUEST_LOGS = "request_logs"
COLLECTION_ERROR_LOGS = "error_logs"
COLLECTION_CONVERSATIONS = "conversations"

# Conversation Memory Configuration
MAX_CONVERSATION_MESSAGES = 10  # Maximum number of previous messages to include
MAX_CONVERSATION_TOKENS = 2000  # Maximum estimated tokens for conversation history

# API Response Messages
MESSAGES = {
    "SUCCESS": "Request processed successfully",
    "ERROR": "An error occurred while processing your request",
    "INVALID_PROMPT": "Prompt is required and cannot be empty",
    "GITHUB_ERROR": "Error accessing GitHub repositories",
    "GROQ_ERROR": "Error communicating with AI service",
}

