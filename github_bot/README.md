# GitHub Bot - Backend API

A Django REST Framework API for chatting with an AI assistant that has access to your GitHub repositories.

## Project Structure

```
github_bot/
├── constants.py              # System prompts and configuration constants
├── serializers.py            # DRF serializers for request/response validation
├── urls.py                   # URL routing for the app
├── views/                    # API views (minimal code)
│   ├── __init__.py
│   └── chat_views.py         # Chat API endpoint
├── utils/                    # Business logic
│   ├── __init__.py
│   ├── database.py           # MongoDB connection and logging utilities
│   ├── github_service.py    # GitHub API integration
│   ├── gemini_service.py    # Gemini AI integration
│   └── chat_service.py      # Main chat orchestration service
└── templates/                # Jinja2 templates (for future frontend)
    └── github_bot/
```

## Architecture

### Separation of Concerns

- **Views** (`views/`): Minimal API code - only handle HTTP requests/responses
- **Utils** (`utils/`): All business logic and service integrations
- **Constants** (`constants.py`): Configuration and system prompts
- **Serializers** (`serializers.py`): Request/response validation

### Services

1. **ChatService**: Orchestrates the chat flow
   - Validates prompts
   - Fetches repository context
   - Generates AI responses
   - Logs interactions

2. **GitHubService**: Handles GitHub API interactions
   - Fetches user repositories
   - Gets repository details
   - Retrieves file contents
   - Builds repository context

3. **GeminiService**: Handles AI interactions
   - Sends prompts to Gemini
   - Includes system instructions
   - Processes responses

4. **Database Utilities**: MongoDB operations
   - Chat logs
   - Request/response logs
   - Error logs

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
   - `GEMINI_API_KEY`
   - `GITHUB_PAT`
   - `MONGODB_URI`
   - `MONGODB_DB_NAME`

3. Run migrations (if using Django models):
```bash
python manage.py migrate
```

4. Start the server:
```bash
python manage.py runserver
```

## API Endpoint

**POST** `/api/chat/`

See `API_DOCUMENTATION.md` for detailed API documentation.

## Database Collections

All interactions are logged to MongoDB:

- `chat_logs`: User prompts and AI responses
- `request_logs`: Request/response metadata and performance metrics
- `error_logs`: Error tracking and debugging information

## Error Handling

All errors are:
1. Logged to MongoDB (`error_logs` collection)
2. Returned with appropriate HTTP status codes
3. Include helpful error messages for debugging

## Future Enhancements

- Authentication and user management
- Conversation history
- Repository-specific queries
- Code analysis features
- Rate limiting
- Caching for frequently accessed repositories

