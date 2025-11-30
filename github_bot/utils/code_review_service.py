"""
Code review service for analyzing code quality and suggesting improvements.
"""
import logging
from typing import Dict, Any, Optional, List
from github_bot.utils.groq_service import GroqService
from github_bot.utils.database import save_error_log

logger = logging.getLogger(__name__)


class CodeReviewService:
    """Service for AI-powered code review and analysis."""
    
    def __init__(self):
        self.groq_service = GroqService()
    
    def review_code(
        self,
        code: str,
        language: str = "python",
        context: Optional[str] = None,
        model_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Review code and provide suggestions for improvement.
        
        Args:
            code: Code to review
            language: Programming language (default: python)
            context: Additional context about the code
            model_id: Groq model ID to use
        
        Returns:
            Dictionary with review results
        """
        try:
            if not code or not code.strip():
                return {
                    "success": False,
                    "error": "No code provided for review"
                }
            
            # Build review prompt
            review_prompt = self._build_review_prompt(code, language, context)
            
            # Get AI review
            logger.info(f"Reviewing {language} code ({len(code)} chars)")
            review_response = self.groq_service.chat(
                prompt=review_prompt,
                model_id=model_id,
                system_instruction=self._get_review_system_instruction()
            )
            
            if not review_response:
                return {
                    "success": False,
                    "error": "Failed to generate code review"
                }
            
            # Parse review response
            review_data = self._parse_review_response(review_response)
            
            return {
                "success": True,
                "review": review_data,
                "language": language,
                "code_length": len(code)
            }
            
        except Exception as e:
            error_msg = f"Error reviewing code: {str(e)}"
            logger.error(error_msg, exc_info=True)
            save_error_log(
                error_type="CodeReviewError",
                error_message=error_msg,
                context={"language": language, "code_length": len(code) if code else 0}
            )
            return {
                "success": False,
                "error": "An error occurred during code review"
            }
    
    def analyze_file(
        self,
        file_content: str,
        file_path: str,
        model_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze a complete file for code quality issues.
        
        Args:
            file_content: Content of the file
            file_path: Path to the file (for language detection)
            model_id: Groq model ID to use
        
        Returns:
            Dictionary with analysis results
        """
        try:
            # Detect language from file extension
            language = self._detect_language(file_path)
            
            # For large files, focus on key issues
            if len(file_content) > 5000:
                logger.info(f"Large file detected ({len(file_content)} chars), using focused analysis")
                return self._analyze_large_file(file_content, language, file_path, model_id)
            
            # Review the file
            return self.review_code(
                code=file_content,
                language=language,
                context=f"File: {file_path}",
                model_id=model_id
            )
            
        except Exception as e:
            error_msg = f"Error analyzing file: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "Failed to analyze file"
            }
    
    def suggest_improvements(
        self,
        code: str,
        language: str = "python",
        focus_areas: Optional[List[str]] = None,
        model_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Suggest specific improvements for code.
        
        Args:
            code: Code to improve
            language: Programming language
            focus_areas: Specific areas to focus on (e.g., ['performance', 'readability'])
            model_id: Groq model ID to use
        
        Returns:
            Dictionary with improvement suggestions
        """
        try:
            focus = focus_areas or ['all']
            focus_str = ", ".join(focus)
            
            prompt = f"""Analyze this {language} code and suggest improvements focusing on: {focus_str}

Code:
```{language}
{code}
```

Provide specific, actionable suggestions with examples where possible."""
            
            response = self.groq_service.chat(
                prompt=prompt,
                model_id=model_id,
                system_instruction=self._get_improvement_system_instruction()
            )
            
            if not response:
                return {
                    "success": False,
                    "error": "Failed to generate suggestions"
                }
            
            return {
                "success": True,
                "suggestions": response,
                "focus_areas": focus,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error suggesting improvements: {str(e)}")
            return {
                "success": False,
                "error": "Failed to generate improvement suggestions"
            }
    
    def _build_review_prompt(self, code: str, language: str, context: Optional[str]) -> str:
        """Build the code review prompt."""
        prompt = f"Review this {language} code:\n\n```{language}\n{code}\n```\n\n"
        
        if context:
            prompt += f"Context: {context}\n\n"
        
        prompt += """Please provide:
1. **Overall Assessment**: Brief summary of code quality
2. **Strengths**: What's done well
3. **Issues**: Problems found (bugs, security, performance)
4. **Suggestions**: Specific improvements with examples
5. **Best Practices**: Recommendations for better code

Format your response in clear sections with markdown."""
        
        return prompt
    
    def _get_review_system_instruction(self) -> str:
        """Get system instruction for code review."""
        return """You are an expert code reviewer with deep knowledge of software engineering best practices.

Your reviews should be:
- **Constructive**: Focus on improvement, not criticism
- **Specific**: Provide concrete examples and suggestions
- **Prioritized**: Highlight critical issues first
- **Educational**: Explain why something is an issue
- **Practical**: Suggest realistic improvements

Consider:
- Code quality and maintainability
- Performance and efficiency
- Security vulnerabilities
- Best practices and design patterns
- Error handling and edge cases
- Code readability and documentation"""
    
    def _get_improvement_system_instruction(self) -> str:
        """Get system instruction for improvement suggestions."""
        return """You are a code optimization expert who helps developers write better code.

Provide:
- Clear, actionable suggestions
- Before/after code examples
- Explanation of benefits
- Priority levels (critical, important, nice-to-have)

Focus on:
- Performance optimization
- Code readability
- Maintainability
- Security
- Best practices"""
    
    def _parse_review_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI review response into structured data."""
        # For now, return the full response
        # In future, could parse into sections
        return {
            "full_review": response,
            "formatted": True
        }
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.cs': 'csharp',
            '.jsx': 'react',
            '.tsx': 'react-typescript',
            '.vue': 'vue',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'bash',
        }
        
        for ext, lang in ext_map.items():
            if file_path.lower().endswith(ext):
                return lang
        
        return 'text'
    
    def _analyze_large_file(
        self,
        file_content: str,
        language: str,
        file_path: str,
        model_id: Optional[int]
    ) -> Dict[str, Any]:
        """Analyze large files with focused approach."""
        # Take first 2000 chars and last 1000 chars
        preview = file_content[:2000] + "\n\n... [middle content omitted] ...\n\n" + file_content[-1000:]
        
        prompt = f"""Analyze this {language} file for major issues:

File: {file_path}
Size: {len(file_content)} characters

Preview:
```{language}
{preview}
```

Focus on:
- Critical bugs or security issues
- Major design problems
- Performance bottlenecks
- Missing error handling

Provide a concise summary of key findings."""
        
        response = self.groq_service.chat(
            prompt=prompt,
            model_id=model_id,
            system_instruction=self._get_review_system_instruction()
        )
        
        return {
            "success": True,
            "review": {
                "full_review": response,
                "is_preview": True,
                "file_size": len(file_content)
            },
            "language": language
        }
