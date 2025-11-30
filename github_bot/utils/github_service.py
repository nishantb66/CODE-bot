"""
GitHub API service utility for accessing repositories and code.
"""
import os
import requests
import logging
import base64
from typing import List, Dict, Any, Optional
from github_bot.utils.database import save_error_log
from github_bot.utils.cache import github_cache

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self, use_cache: bool = True):
        self.pat_token = os.environ.get('GITHUB_PAT')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.pat_token}" if self.pat_token else None
        }
        self.use_cache = use_cache
        
        if not self.pat_token:
            logger.warning("GitHub PAT token not found in environment variables")
    
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to GitHub API.
        
        Args:
            endpoint: API endpoint (e.g., '/user/repos')
            method: HTTP method
            **kwargs: Additional request parameters
        
        Returns:
            Response data as dictionary or None if error
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"GitHub API request failed: {str(e)}"
            logger.error(error_msg)
            save_error_log(
                error_type="GitHubAPIError",
                error_message=error_msg,
                context={"endpoint": endpoint, "method": method}
            )
            return None
    
    def get_user_repositories(self) -> List[Dict[str, Any]]:
        """
        Get all repositories for the authenticated user.
        Uses caching to reduce API calls.
        
        Returns:
            List of repository dictionaries
        """
        cache_key = "user_repos"
        
        # Try cache first
        if self.use_cache:
            cached = github_cache.get(cache_key)
            if cached is not None:
                logger.debug("Returning cached user repositories")
                return cached
        
        try:
            repos = self._make_request("/user/repos", params={"per_page": 100, "sort": "updated"})
            result = repos if repos else []
            
            # Cache the result
            if self.use_cache and result:
                github_cache.set(cache_key, result, ttl_seconds=300)  # 5 minutes
            
            return result
        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            return []
    
    def get_repository_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific repository.
        
        Args:
            owner: Repository owner username
            repo: Repository name
        
        Returns:
            Repository information dictionary or None
        """
        return self._make_request(f"/repos/{owner}/{repo}")
    
    def get_repository_contents(self, owner: str, repo: str, path: str = "") -> Optional[List[Dict[str, Any]]]:
        """
        Get contents of a repository directory or file.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            path: Path within repository (empty for root)
        
        Returns:
            List of file/directory items or None
        """
        return self._make_request(f"/repos/{owner}/{repo}/contents/{path}")
    
    def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """
        Get content of a specific file.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            path: File path within repository
        
        Returns:
            File content as string or None
        """
        try:
            file_info = self._make_request(f"/repos/{owner}/{repo}/contents/{path}")
            if file_info and "content" in file_info:
                content = base64.b64decode(file_info["content"]).decode('utf-8')
                return content
            return None
        except Exception as e:
            logger.error(f"Error fetching file content: {str(e)}")
            return None
    
    def search_repositories(self, query: str) -> List[Dict[str, Any]]:
        """
        Search repositories by query.
        
        Args:
            query: Search query
        
        Returns:
            List of matching repositories
        """
        try:
            results = self._make_request("/search/repositories", params={"q": query})
            if results and "items" in results:
                return results["items"]
            return []
        except Exception as e:
            logger.error(f"Error searching repositories: {str(e)}")
            return []
    
    def get_repository_tree(self, owner: str, repo: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Get repository file tree structure without fetching file contents.
        Uses caching to reduce API calls.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            max_depth: Maximum depth to traverse (default: 2)
        
        Returns:
            Dictionary with tree structure and metadata
        """
        cache_key = f"repo_tree:{owner}/{repo}:{max_depth}"
        
        # Try cache first
        if self.use_cache:
            cached = github_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Returning cached repository tree for {owner}/{repo}")
                return cached
        
        try:
            # Get the default branch
            repo_info = self.get_repository_info(owner, repo)
            if not repo_info:
                return {"files": [], "directories": [], "total_files": 0}
            
            default_branch = repo_info.get("default_branch", "main")
            
            # Get tree via Git Trees API (more efficient)
            tree_data = self._make_request(
                f"/repos/{owner}/{repo}/git/trees/{default_branch}",
                params={"recursive": "1"}
            )
            
            if not tree_data or "tree" not in tree_data:
                return {"files": [], "directories": [], "total_files": 0}
            
            files = []
            directories = []
            
            for item in tree_data["tree"]:
                # Limit depth
                path_depth = item["path"].count("/")
                if path_depth > max_depth:
                    continue
                
                if item["type"] == "blob":  # File
                    files.append({
                        "path": item["path"],
                        "size": item.get("size", 0),
                        "type": self._get_file_type(item["path"])
                    })
                elif item["type"] == "tree":  # Directory
                    directories.append(item["path"])
            
            result = {
                "files": files,
                "directories": directories,
                "total_files": len(files),
                "total_directories": len(directories)
            }
            
            # Cache the result (longer TTL for tree structure)
            if self.use_cache:
                github_cache.set(cache_key, result, ttl_seconds=600)  # 10 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching repository tree: {str(e)}")
            return {"files": [], "directories": [], "total_files": 0}
    
    def _get_file_type(self, path: str) -> str:
        """Determine file type from extension."""
        ext_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".java": "java", ".cpp": "cpp", ".c": "c", ".go": "go",
            ".rs": "rust", ".rb": "ruby", ".php": "php", ".swift": "swift",
            ".kt": "kotlin", ".md": "markdown", ".json": "json",
            ".yaml": "yaml", ".yml": "yaml", ".xml": "xml", ".html": "html",
            ".css": "css", ".sql": "sql", ".sh": "shell"
        }
        
        for ext, file_type in ext_map.items():
            if path.lower().endswith(ext):
                return file_type
        return "other"
    
    def get_important_files(self, owner: str, repo: str, max_files: int = 5) -> List[Dict[str, Any]]:
        """
        Identify and fetch important files from a repository.
        
        Args:
            owner: Repository owner username
            repo: Repository name
            max_files: Maximum number of files to fetch (default: 5)
        
        Returns:
            List of important files with content summaries
        """
        try:
            tree = self.get_repository_tree(owner, repo, max_depth=2)
            files = tree.get("files", [])
            
            # Priority order for important files
            priority_patterns = [
                ("readme.md", 100),
                ("readme.txt", 90),
                ("readme", 85),
                ("main.py", 80),
                ("app.py", 75),
                ("index.js", 75),
                ("main.js", 75),
                ("package.json", 70),
                ("requirements.txt", 70),
                ("setup.py", 65),
                ("config", 60),
                (".env.example", 55),
            ]
            
            # Score files based on importance
            scored_files = []
            for file in files:
                path_lower = file["path"].lower()
                score = 0
                
                # Check priority patterns
                for pattern, pattern_score in priority_patterns:
                    if pattern in path_lower:
                        score = max(score, pattern_score)
                
                # Boost score for root-level files
                if "/" not in file["path"]:
                    score += 20
                
                # Boost score for common source files
                if file["type"] in ["python", "javascript", "typescript", "java"]:
                    score += 10
                
                if score > 0:
                    scored_files.append((file, score))
            
            # Sort by score and take top files
            scored_files.sort(key=lambda x: x[1], reverse=True)
            top_files = [f[0] for f in scored_files[:max_files]]
            
            # Fetch content for top files
            important_files = []
            for file in top_files:
                content = self.get_file_content(owner, repo, file["path"])
                if content:
                    # Truncate large files
                    summary = self.extract_code_summary(content, file["type"])
                    important_files.append({
                        "path": file["path"],
                        "type": file["type"],
                        "summary": summary,
                        "size": file.get("size", 0)
                    })
            
            return important_files
            
        except Exception as e:
            logger.error(f"Error fetching important files: {str(e)}")
            return []
    
    def extract_code_summary(self, content: str, file_type: str, max_lines: int = 50) -> str:
        """
        Extract a summary from code content.
        
        Args:
            content: File content
            file_type: Type of file (python, javascript, etc.)
            max_lines: Maximum lines to include (default: 50)
        
        Returns:
            Summarized content
        """
        try:
            lines = content.split("\n")
            
            # If file is small enough, return as-is
            if len(lines) <= max_lines:
                return content
            
            # For large files, extract key parts
            summary_lines = []
            
            # Always include first 20 lines (usually imports, headers, docstrings)
            summary_lines.extend(lines[:20])
            summary_lines.append("\n... [content truncated] ...\n")
            
            # Extract function/class definitions
            if file_type == "python":
                for i, line in enumerate(lines[20:], start=20):
                    if line.strip().startswith(("def ", "class ", "async def ")):
                        # Include the definition and docstring
                        summary_lines.append(line)
                        # Look for docstring
                        if i + 1 < len(lines) and '"""' in lines[i + 1]:
                            j = i + 1
                            while j < len(lines) and j < i + 5:
                                summary_lines.append(lines[j])
                                if j > i + 1 and '"""' in lines[j]:
                                    break
                                j += 1
                    
                    if len(summary_lines) > max_lines:
                        break
            
            elif file_type in ["javascript", "typescript"]:
                for i, line in enumerate(lines[20:], start=20):
                    if any(keyword in line for keyword in ["function ", "class ", "const ", "export "]):
                        summary_lines.append(line)
                    
                    if len(summary_lines) > max_lines:
                        break
            
            else:
                # For other file types, just take first and last portions
                summary_lines.extend(lines[20:35])
                summary_lines.append("\n... [middle content truncated] ...\n")
                summary_lines.extend(lines[-10:])
            
            return "\n".join(summary_lines[:max_lines])
            
        except Exception as e:
            logger.error(f"Error extracting code summary: {str(e)}")
            # Return first max_lines if extraction fails
            return "\n".join(content.split("\n")[:max_lines])
    
    def get_smart_repository_context(self, query: str, owner: str, repo: str) -> str:
        """
        Build intelligent repository context based on user query.
        
        Args:
            query: User's question/query
            owner: Repository owner
            repo: Repository name
        
        Returns:
            Formatted context string optimized for the query
        """
        try:
            query_lower = query.lower()
            context_parts = []
            
            # Get basic repo info
            repo_info = self.get_repository_info(owner, repo)
            if repo_info:
                context_parts.append(f"Repository: {repo_info['name']}")
                if repo_info.get('description'):
                    context_parts.append(f"Description: {repo_info['description']}")
                context_parts.append(f"Language: {repo_info.get('language', 'N/A')}")
                context_parts.append(f"Stars: {repo_info.get('stargazers_count', 0)}")
                context_parts.append("")
            
            # Determine what kind of information is needed
            needs_code = any(word in query_lower for word in [
                "code", "function", "class", "implementation", "how does", "show me"
            ])
            
            needs_structure = any(word in query_lower for word in [
                "structure", "files", "organization", "contains", "what files"
            ])
            
            if needs_code:
                # Fetch important files with code
                important_files = self.get_important_files(owner, repo, max_files=3)
                if important_files:
                    context_parts.append("Key Files:")
                    for file in important_files:
                        context_parts.append(f"\n--- {file['path']} ({file['type']}) ---")
                        context_parts.append(file['summary'][:500])  # Limit each file summary
                        context_parts.append("")
            
            elif needs_structure:
                # Fetch file tree
                tree = self.get_repository_tree(owner, repo, max_depth=2)
                if tree:
                    context_parts.append(f"Repository Structure ({tree['total_files']} files):")
                    
                    # Group files by type
                    files_by_type = {}
                    for file in tree.get("files", [])[:30]:  # Limit to 30 files
                        file_type = file["type"]
                        if file_type not in files_by_type:
                            files_by_type[file_type] = []
                        files_by_type[file_type].append(file["path"])
                    
                    for file_type, paths in files_by_type.items():
                        context_parts.append(f"\n{file_type.capitalize()} files:")
                        for path in paths[:10]:  # Max 10 per type
                            context_parts.append(f"  - {path}")
            
            else:
                # Default: fetch README and basic structure
                readme_content = self.get_file_content(owner, repo, "README.md")
                if readme_content:
                    context_parts.append("README:")
                    context_parts.append(readme_content[:800])  # First 800 chars
                    context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building smart repository context: {str(e)}")
            return f"Repository: {owner}/{repo} (context unavailable)"

    def _format_repo_context(self, repos: List[Dict[str, Any]], title: str = "") -> str:
        """
        Helper to format a list of repositories into a string context.
        
        Args:
            repos: List of repository dictionaries
            title: Optional title for the context section
            
        Returns:
            Formatted string
        """
        if not repos:
            return ""
            
        context = f"{title}\n\n" if title else ""
        
        for repo in repos:
            name = repo['name']
            lang = repo.get('language', 'N/A')
            desc = repo.get('description', '')
            stars = repo.get('stargazers_count', 0)
            
            # Truncate description if too long
            if desc and len(desc) > 60:
                desc = desc[:57] + "..."
            
            # Very concise format: name (lang) - desc - ⭐stars
            repo_line = f"- {name} ({lang})"
            if desc:
                repo_line += f": {desc}"
            repo_line += f" ⭐{stars}\n"
            
            context += repo_line
            
        return context
    
    def get_repository_context(self, max_repos: int = 10, max_context_length: int = 1500) -> str:
        """
        Get concise context about user repositories, optimized for token usage.
        
        Args:
            max_repos: Maximum number of repositories to include (default: 10)
            max_context_length: Maximum character length of context (default: 1500)
        
        Returns:
            Formatted string with repository information (token-optimized)
        """
        try:
            repos = self.get_user_repositories()
            if not repos:
                return "No repositories found."
            
            # Sort by stars (most popular first) and limit
            sorted_repos = sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
            repos_to_include = sorted_repos[:max_repos]
            
            # Build concise context
            title = f"User has {len(repos)} repositories. Top {len(repos_to_include)}:"
            context = self._format_repo_context(repos_to_include, title)
            
            if len(repos) > max_repos:
                context += f"\n... and {len(repos) - max_repos} more repositories."
            
            # Final length check
            if len(context) > max_context_length:
                context = context[:max_context_length] + "..."
            
            logger.info(f"Repository context length: {len(context)} characters")
            return context
            
        except Exception as e:
            logger.error(f"Error building repository context: {str(e)}")
            return "Error fetching repository information."
    
    def get_repository_context_for_query(self, query: str, max_repos: int = 5) -> str:
        """
        Get repository context optimized for a specific query.
        Only includes relevant repositories to minimize token usage.
        
        Args:
            query: User's query to determine relevance
            max_repos: Maximum number of repositories to include
        
        Returns:
            Formatted string with relevant repository information
        """
        try:
            repos = self.get_user_repositories()
            if not repos:
                return "No repositories found."
            
            # If query mentions specific repo names, prioritize those
            query_lower = query.lower()
            relevant_repos = []
            other_repos = []
            
            for repo in repos:
                repo_name_lower = repo['name'].lower()
                desc_lower = (repo.get('description', '') or '').lower()
                
                # Check if query mentions this repo
                if repo_name_lower in query_lower or any(word in desc_lower for word in query_lower.split() if len(word) > 3):
                    relevant_repos.append(repo)
                else:
                    other_repos.append(repo)
            
            # Prioritize relevant repos, then most popular
            repos_to_include = relevant_repos[:max_repos]
            if len(repos_to_include) < max_repos:
                remaining = max_repos - len(repos_to_include)
                sorted_others = sorted(other_repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
                repos_to_include.extend(sorted_others[:remaining])
            
            # Build concise context
            title = f"Found {len(relevant_repos)} relevant repositories:" if relevant_repos else f"Top {len(repos_to_include)} repositories:"
            context = self._format_repo_context(repos_to_include, title)
            
            if len(repos) > max_repos:
                context += f"\nTotal: {len(repos)} repositories available."
            
            logger.info(f"Query-optimized context length: {len(context)} characters")
            return context
            
        except Exception as e:
            logger.error(f"Error building query-optimized context: {str(e)}")
            return self.get_repository_context(max_repos=max_repos)

