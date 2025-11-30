# GitHub Bot API Documentation

## Overview

The GitHub Bot API allows users to chat with an AI assistant that has access to their GitHub repositories. The bot can answer questions about repositories, code, and provide insights using Gemini AI.

## Base URL

```
http://localhost:8000/api/
```

## Endpoints

### Chat with GitHub Bot

**Endpoint:** `POST /api/chat/`

**Description:** Send a prompt/question to the GitHub bot and receive an AI-generated response based on your repositories.

**Request Body:**
```json
{
    "prompt": "What repositories do I have?"
}
```

**Request Parameters:**
- `prompt` (string, required): User's question or prompt. Maximum length: 5000 characters.

**Response (Success):**
```json
{
    "success": true,
    "response": "You have access to 15 repositories:\n\n- **project1** (Python)\n  Description: My first project\n  Stars: 10, Forks: 2, Watchers: 5\n  ...",
    "metadata": {
        "duration_ms": 1234.56,
        "prompt_length": 25,
        "response_length": 450
    }
}
```

**Response (Error):**
```json
{
    "success": false,
    "response": "An error occurred while processing your request.",
    "error": "GEMINI_ERROR",
    "metadata": {
        "duration_ms": 500.25
    }
}
```

**Status Codes:**
- `200 OK`: Request processed successfully (check `success` field)
- `400 Bad Request`: Invalid request data (missing or invalid prompt)
- `500 Internal Server Error`: Server error occurred

## Example Usage

### Using cURL

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are my most popular repositories?"}'
```

### Using Python (requests)

```python
import requests

url = "http://localhost:8000/api/chat/"
data = {
    "prompt": "What repositories do I have?"
}

response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    print(result["response"])
else:
    print(f"Error: {result.get('error')}")
```

### Using JavaScript (fetch)

```javascript
fetch('http://localhost:8000/api/chat/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        prompt: 'What repositories do I have?'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log(data.response);
    } else {
        console.error('Error:', data.error);
    }
});
```

## Database Collections

The API automatically logs all interactions to MongoDB:

1. **chat_logs**: Stores prompts and responses
2. **request_logs**: Stores request/response metadata and timing
3. **error_logs**: Stores error information for debugging

## Environment Variables

Required environment variables (in `.env` file):

- `GEMINI_API_KEY`: Google Gemini API key
- `GITHUB_PAT`: GitHub Personal Access Token
- `MONGODB_URI`: MongoDB connection string
- `MONGODB_DB_NAME`: MongoDB database name (default: `github_bot_db`)

## Error Handling

The API handles errors gracefully and returns appropriate error messages:

- **VALIDATION_ERROR**: Invalid request data
- **GEMINI_ERROR**: Error communicating with Gemini AI
- **GITHUB_ERROR**: Error accessing GitHub API
- **INTERNAL_ERROR**: Unexpected server error

All errors are logged to MongoDB for debugging purposes.

