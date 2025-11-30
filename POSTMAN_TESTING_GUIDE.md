# Postman Testing Guide for GitHub Bot API

## Server Information
- **Base URL**: `http://127.0.0.1:8000`
- **API Endpoint**: `http://127.0.0.1:8000/api/chat/`
- **Method**: `POST`

## Step-by-Step Postman Setup

### 1. Open Postman
Launch Postman application on your computer.

### 2. Create a New Request
- Click **"New"** button (top left)
- Select **"HTTP Request"**
- Or use shortcut: `Ctrl+N` (Windows/Linux) or `Cmd+N` (Mac)

### 3. Configure the Request

#### Method and URL
- **Method**: Select `POST` from the dropdown (default is GET)
- **URL**: Enter `http://127.0.0.1:8000/api/chat/`

#### Headers
1. Click on the **"Headers"** tab
2. Add the following header:
   - **Key**: `Content-Type`
   - **Value**: `application/json`

#### Body
1. Click on the **"Body"** tab
2. Select **"raw"** radio button
3. From the dropdown on the right, select **"JSON"**
4. Enter the following JSON in the text area:

```json
{
    "prompt": "What repositories do I have?"
}
```

### 4. Send the Request
- Click the **"Send"** button (blue button on the right)
- Wait for the response

## Expected Response

### Success Response (200 OK)
```json
{
    "success": true,
    "response": "You have access to X repositories:\n\n- **repo1** (Python)\n  Description: ...\n  ...",
    "metadata": {
        "duration_ms": 1234.56,
        "prompt_length": 25,
        "response_length": 450
    }
}
```

### Error Response (400 Bad Request - Invalid Prompt)
```json
{
    "success": false,
    "response": "Invalid request data.",
    "error": "VALIDATION_ERROR",
    "details": {
        "prompt": ["This field is required."]
    }
}
```

## Test Cases to Try

### Test Case 1: Basic Repository Query
```json
{
    "prompt": "What repositories do I have?"
}
```

### Test Case 2: Specific Repository Question
```json
{
    "prompt": "Tell me about my most popular repository"
}
```

### Test Case 3: Repository Count
```json
{
    "prompt": "How many repositories do I have?"
}
```

### Test Case 4: Language-based Query
```json
{
    "prompt": "What programming languages are used in my repositories?"
}
```

### Test Case 5: Empty Prompt (Should Fail)
```json
{
    "prompt": ""
}
```

### Test Case 6: Missing Prompt (Should Fail)
```json
{}
```

## Troubleshooting

### Issue: Connection Refused
**Error**: `Could not get any response`

**Solution**:
1. Make sure the Django server is running
2. Check if the server is running on port 8000
3. Verify the URL is correct: `http://127.0.0.1:8000/api/chat/`

### Issue: 404 Not Found
**Error**: `404 Not Found`

**Solution**:
1. Check the URL path: Should be `/api/chat/` (with trailing slash)
2. Verify the server is running
3. Check `analyzer/urls.py` to confirm the route is configured

### Issue: 500 Internal Server Error
**Error**: `500 Internal Server Error`

**Possible Causes**:
1. MongoDB connection issue - Check MongoDB URI in `.env`
2. GitHub API token issue - Verify GITHUB_PAT in `.env`
3. Gemini API key issue - Verify GEMINI_API_KEY in `.env`

**Solution**:
- Check server logs in the terminal where `runserver` is running
- Verify all environment variables are set correctly in `.env` file

### Issue: Invalid JSON
**Error**: `400 Bad Request` with JSON parsing error

**Solution**:
1. Make sure you selected "JSON" in the Body dropdown
2. Verify the JSON syntax is correct (no trailing commas, proper quotes)
3. Ensure Content-Type header is set to `application/json`

## Quick Test with cURL (Alternative)

If you prefer command line, you can also test with cURL:

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What repositories do I have?"}'
```

## Response Time
- Normal response time: 2-5 seconds
- Includes time for:
  - GitHub API calls
  - Gemini AI processing
  - MongoDB logging

## Notes
- The API automatically logs all requests to MongoDB
- Check the server terminal for detailed logs
- All errors are logged to MongoDB `error_logs` collection
- Response includes metadata with timing information

