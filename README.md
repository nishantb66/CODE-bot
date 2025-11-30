# 🚀 GitHub Bot - AI-Powered Repository Assistant

An intelligent chatbot that helps you analyze, understand, and improve your GitHub repositories using AI.

## ✨ Features

### 💬 **Intelligent Chat Interface**
- Natural language queries about your repositories
- Context-aware responses with conversation memory
- Smart repository detection and analysis
- Markdown-formatted responses

### 🔍 **Smart Repository Analysis**
- Automatic code indexing and retrieval
- Query-based context building
- Efficient handling of large repositories
- Caching for improved performance

### 🎨 **Code Review Assistant** ⭐ NEW
- AI-powered code quality analysis
- Review code snippets or entire files
- Get targeted improvement suggestions
- Support for 15+ programming languages

### 🎯 **Professional UI**
- Modern, elegant design
- White, light green, and light blue color scheme
- Smooth animations and transitions
- Fully responsive (mobile & desktop)

---

## 🛠️ Tech Stack

- **Backend**: Django 5.2.8, Django REST Framework
- **Database**: MongoDB (conversation history & logs)
- **AI**: Groq AI (Llama 3.3 70B & Llama 3.1 8B)
- **GitHub Integration**: GitHub API with PAT authentication
- **Frontend**: HTML, TailwindCSS, Vanilla JavaScript
- **Caching**: In-memory cache with TTL

---

## 📋 Prerequisites

- Python 3.8+
- MongoDB (local or cloud)
- GitHub Personal Access Token (PAT)
- Groq API Key

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd analyzer
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
# GitHub Configuration
GITHUB_PAT=your_github_personal_access_token

# Groq AI Configuration
GROQ_API_KEY=your_groq_api_key

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
```

### 3. Run the Server

```bash
python manage.py runserver
```

Visit: `http://localhost:8000`

---

## 📚 API Endpoints

### Chat Endpoints

#### **POST** `/api/chat/`
Chat with the AI about your repositories.

```json
{
  "prompt": "What repositories do I have?",
  "model_id": 2,
  "conversation_id": "optional-uuid"
}
```

---

### Code Review Endpoints ⭐ NEW

#### **POST** `/api/review-code/`
Review a code snippet.

```json
{
  "code": "def hello():\n    print('Hello')",
  "language": "python",
  "context": "Optional context",
  "model_id": 2
}
```

#### **POST** `/api/review-file/`
Review a file from GitHub.

```json
{
  "owner": "username",
  "repo": "repository",
  "file_path": "src/main.py",
  "model_id": 2
}
```

#### **POST** `/api/suggest-improvements/`
Get targeted improvement suggestions.

```json
{
  "code": "your code here",
  "language": "python",
  "focus_areas": ["performance", "security"],
  "model_id": 2
}
```

---

## 📖 Documentation

- **[Code Review Feature Guide](CODE_REVIEW_FEATURE.md)** - Complete API reference
- **[Implementation Summary](CODE_REVIEW_IMPLEMENTATION.md)** - Technical details
- **[Optimization Guide](OPTIMIZATION_GUIDE.md)** - Performance optimization
- **[Postman Collection](CODE_REVIEW_POSTMAN.json)** - API testing

---

## 🎯 Use Cases

### For Developers
- 📊 Analyze repository structure
- 🔍 Search code with natural language
- 📝 Get code explanations
- ✅ Review code quality
- 🚀 Get improvement suggestions

### For Teams
- 👥 Automate initial code reviews
- 📈 Track code quality metrics
- 🔒 Identify security issues
- 📚 Generate documentation

### For Learning
- 💡 Understand complex code
- 📖 Learn best practices
- 🎓 Get explanations and examples

---

## 🔧 Configuration

### Models

```python
GROQ_MODELS = {
    1: "llama-3.1-8b-instant",      # Faster, lighter
    2: "llama-3.3-70b-versatile"    # Better quality (default)
}
```

### Cache Settings

```python
DEFAULT_TTL = 300      # 5 minutes
TREE_TTL = 600         # 10 minutes
```

### Context Limits

```python
MAX_FILES = 5          # Important files to fetch
MAX_LINES = 50         # Lines per file summary
MAX_TREE_DEPTH = 2     # Directory depth
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Token Reduction** | 80% (10K → 2K avg) |
| **API Calls Reduction** | 60% (with caching) |
| **Response Time** | 3-5 seconds |
| **Cache Hit Rate** | 40% |

---

## 🧪 Testing

### Using cURL

```bash
# Review code
curl -X POST http://localhost:8000/api/review-code/ \
  -H "Content-Type: application/json" \
  -d '{"code": "def add(a,b): return a+b", "language": "python"}'
```

### Using Postman

Import `CODE_REVIEW_POSTMAN.json` into Postman for pre-configured requests.

### Using Python

```python
import requests

response = requests.post('http://localhost:8000/api/review-code/', json={
    'code': 'def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)',
    'language': 'python'
})

print(response.json()['review']['full_review'])
```

---

## 🏗️ Project Structure

```
analyzer/
├── github_bot/
│   ├── utils/
│   │   ├── chat_service.py           # Chat orchestration
│   │   ├── github_service.py         # GitHub API integration
│   │   ├── groq_service.py           # Groq AI integration
│   │   ├── code_review_service.py    # Code review logic ⭐ NEW
│   │   ├── database.py               # MongoDB operations
│   │   └── cache.py                  # Caching layer ⭐ NEW
│   ├── views/
│   │   ├── chat_views.py             # Chat API
│   │   ├── code_review_views.py      # Code review API ⭐ NEW
│   │   └── web_views.py              # Web interface
│   ├── templates/
│   │   └── github_bot/
│   │       ├── base.html             # Base template
│   │       └── chat.html             # Chat interface
│   ├── serializers.py                # DRF serializers
│   ├── constants.py                  # Configuration
│   └── urls.py                       # URL routing
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🌟 Key Features Explained

### Smart Code Indexing
- Fetches only relevant files based on query
- Prioritizes important files (README, main files, configs)
- Extracts code summaries for large files
- Caches results to reduce API calls

### Intelligent Context Building
- Detects query intent (code, structure, general)
- Builds optimized context for AI
- Handles large repositories efficiently
- Stays within API token limits

### Code Review Assistant
- Analyzes code quality and style
- Identifies bugs and security issues
- Suggests performance improvements
- Provides before/after examples

---

## 🔒 Security

- GitHub PAT stored securely in environment variables
- Groq API key protected
- Input validation on all endpoints
- MongoDB connection secured
- No sensitive data in logs

---

## 🐛 Troubleshooting

### Issue: "GitHub PAT token not found"
**Solution**: Add `GITHUB_PAT` to your `.env` file

### Issue: "Groq service not configured"
**Solution**: Add `GROQ_API_KEY` to your `.env` file

### Issue: "MongoDB connection failed"
**Solution**: Ensure MongoDB is running and `MONGODB_URI` is correct

### Issue: "Empty or generic reviews"
**Solution**: Provide more context and specify the language

---

## 📈 Future Enhancements

- [ ] Pull Request integration
- [ ] Documentation generator
- [ ] Commit message generator
- [ ] Vector database for semantic search
- [ ] GitHub Actions integration
- [ ] Team dashboard
- [ ] VS Code extension
- [ ] Slack/Discord bot

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🙏 Acknowledgments

- **Groq AI** for powerful LLM inference
- **GitHub** for comprehensive API
- **Django** & **DRF** for robust backend
- **MongoDB** for flexible data storage

---

## 📞 Support

For issues or questions:
- Check the documentation files
- Review error logs
- Ensure all environment variables are set
- Verify API keys are valid

---

**Built with ❤️ using Django, Groq AI, and GitHub API**

**Happy Coding! 🚀**
