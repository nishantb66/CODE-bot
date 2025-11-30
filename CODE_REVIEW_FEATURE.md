# Code Review Feature Documentation

## Overview

The **Code Review Assistant** is an AI-powered feature that analyzes code quality, identifies issues, and suggests improvements using Groq AI.

## Features

### 1. **Code Snippet Review**
Review any code snippet and get detailed feedback.

### 2. **File Review from GitHub**
Directly review files from your GitHub repositories.

### 3. **Improvement Suggestions**
Get targeted suggestions for specific areas like performance, readability, or security.

---

## API Endpoints

### 1. Review Code Snippet

**Endpoint**: `POST /api/review-code/`

**Request Body**:
```json
{
  "code": "def calculate_sum(numbers):\n    total = 0\n    for num in numbers:\n        total = total + num\n    return total",
  "language": "python",
  "context": "Function to calculate sum of numbers",
  "model_id": 2
}
```

**Response**:
```json
{
  "success": true,
  "review": {
    "full_review": "## Overall Assessment\n\nThe code is functional but can be improved...",
    "formatted": true
  },
  "language": "python",
  "code_length": 123,
  "metadata": {
    "duration_ms": 1234.56,
    "timestamp": 1234567890
  }
}
```

---

### 2. Review GitHub File

**Endpoint**: `POST /api/review-file/`

**Request Body**:
```json
{
  "owner": "username",
  "repo": "repository-name",
  "file_path": "src/utils/helper.py",
  "model_id": 2
}
```

**Response**:
```json
{
  "success": true,
  "review": {
    "full_review": "## Code Review for helper.py\n\n...",
    "formatted": true
  },
  "language": "python",
  "metadata": {
    "duration_ms": 2345.67,
    "file_path": "src/utils/helper.py",
    "repository": "username/repository-name"
  }
}
```

---

### 3. Get Improvement Suggestions

**Endpoint**: `POST /api/suggest-improvements/`

**Request Body**:
```json
{
  "code": "def process_data(data):\n    result = []\n    for item in data:\n        if item > 0:\n            result.append(item * 2)\n    return result",
  "language": "python",
  "focus_areas": ["performance", "readability"],
  "model_id": 2
}
```

**Response**:
```json
{
  "success": true,
  "suggestions": "## Improvement Suggestions\n\n### Performance\n- Use list comprehension...",
  "focus_areas": ["performance", "readability"],
  "language": "python",
  "metadata": {
    "duration_ms": 1567.89,
    "timestamp": 1234567890
  }
}
```

---

## Usage Examples

### Python Example

```python
import requests

# Review code snippet
response = requests.post('http://localhost:8000/api/review-code/', json={
    "code": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """,
    "language": "python",
    "context": "Recursive fibonacci implementation"
})

result = response.json()
print(result['review']['full_review'])
```

### JavaScript Example

```javascript
// Review GitHub file
fetch('http://localhost:8000/api/review-file/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    owner: 'myusername',
    repo: 'my-project',
    file_path: 'src/index.js',
    model_id: 2
  })
})
.then(response => response.json())
.then(data => console.log(data.review.full_review));
```

### cURL Example

```bash
# Get improvement suggestions
curl -X POST http://localhost:8000/api/suggest-improvements/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "for i in range(len(items)):\n    print(items[i])",
    "language": "python",
    "focus_areas": ["readability", "pythonic"]
  }'
```

---

## Review Output Format

The AI provides structured reviews with the following sections:

### 1. **Overall Assessment**
Brief summary of code quality and main findings.

### 2. **Strengths**
What's done well in the code.

### 3. **Issues**
Problems categorized by:
- 🐛 **Bugs**: Logic errors or potential crashes
- 🔒 **Security**: Vulnerabilities or unsafe practices
- ⚡ **Performance**: Inefficiencies or bottlenecks
- 📝 **Code Quality**: Style, naming, structure issues

### 4. **Suggestions**
Specific improvements with:
- Before/after code examples
- Explanation of benefits
- Priority level

### 5. **Best Practices**
Recommendations for better code following industry standards.

---

## Supported Languages

- Python
- JavaScript / TypeScript
- Java
- C / C++
- Go
- Rust
- Ruby
- PHP
- Swift
- Kotlin
- C#
- HTML / CSS
- SQL
- Bash / Shell
- And more...

---

## Focus Areas for Improvements

When using `/api/suggest-improvements/`, you can specify focus areas:

- **`performance`**: Speed and efficiency optimizations
- **`readability`**: Code clarity and maintainability
- **`security`**: Vulnerability detection and fixes
- **`best-practices`**: Industry standard patterns
- **`error-handling`**: Exception and edge case handling
- **`testing`**: Testability improvements
- **`documentation`**: Code comments and docstrings
- **`all`**: Comprehensive review (default)

---

## Best Practices

### 1. **Provide Context**
```json
{
  "code": "...",
  "context": "This function processes user authentication tokens"
}
```

### 2. **Specify Language**
Always specify the programming language for accurate analysis.

### 3. **Focus Your Review**
Use `focus_areas` to get targeted suggestions:
```json
{
  "code": "...",
  "focus_areas": ["security", "performance"]
}
```

### 4. **Review Small Chunks**
For best results, review functions or classes individually rather than entire files.

### 5. **Iterate**
Apply suggestions and re-review to ensure improvements.

---

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "success": false,
  "error": "Invalid request data",
  "details": {
    "code": ["This field is required."]
  }
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Failed to fetch file from GitHub. Please check the repository and file path."
}
```

**500 Internal Server Error**
```json
{
  "success": false,
  "error": "An error occurred while reviewing code"
}
```

---

## Performance Considerations

### File Size Limits

- **Small files** (<5000 chars): Full analysis
- **Large files** (>5000 chars): Focused analysis on key issues

### Response Times

- **Code snippet review**: 1-3 seconds
- **File review**: 2-5 seconds
- **Improvement suggestions**: 1-3 seconds

### Rate Limits

Respects Groq AI free tier limits:
- Monitor your API usage
- Implement caching for frequently reviewed files
- Use appropriate model (model_id: 1 for faster, 2 for better quality)

---

## Integration Examples

### Add to Your Chat Interface

```javascript
// Add code review button to chat
function reviewCode(code, language) {
  fetch('/api/review-code/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, language, model_id: 2 })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      displayReview(data.review.full_review);
    }
  });
}
```

### GitHub Actions Integration

```yaml
# .github/workflows/code-review.yml
name: AI Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Review Changed Files
        run: |
          # Call your API to review changed files
          curl -X POST ${{ secrets.REVIEW_API_URL }}/api/review-file/ \
            -d '{"owner":"${{ github.repository_owner }}", ...}'
```

---

## Advanced Usage

### Batch Review Multiple Files

```python
def review_repository(owner, repo, file_paths):
    """Review multiple files from a repository."""
    reviews = []
    for file_path in file_paths:
        response = requests.post('http://localhost:8000/api/review-file/', json={
            'owner': owner,
            'repo': repo,
            'file_path': file_path,
            'model_id': 2
        })
        reviews.append(response.json())
    return reviews
```

### Custom Review Prompts

The system uses intelligent prompts that can be customized in `code_review_service.py`:

```python
# Customize review focus
review_service = CodeReviewService()
result = review_service.review_code(
    code=my_code,
    language="python",
    context="Focus on security vulnerabilities and SQL injection risks"
)
```

---

## Troubleshooting

### Issue: Empty or Generic Reviews

**Solution**: Provide more context and specify the language accurately.

### Issue: Timeout Errors

**Solution**: Break large files into smaller chunks or use focused analysis.

### Issue: Inaccurate Suggestions

**Solution**: Ensure the correct language is specified and provide relevant context.

---

## Future Enhancements

- [ ] Pull Request integration
- [ ] Automated fix suggestions
- [ ] Code diff analysis
- [ ] Team review dashboard
- [ ] Custom review templates
- [ ] Integration with CI/CD pipelines

---

## Support

For issues or questions:
1. Check the error message in the response
2. Review the server logs
3. Ensure your GitHub PAT and Groq API key are valid
4. Verify the file path and repository access

---

**Happy Coding! 🚀**
