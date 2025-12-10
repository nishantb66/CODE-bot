"""
Enhanced Repository Report Generation Service
Generates comprehensive AI-powered PDF reports for GitHub repositories
"""
import os
import io
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import requests
from typing import Dict, Any, Optional, List
from groq import Groq


class EnhancedReportGenerator:
    """Generate professional AI-powered PDF reports for GitHub repositories"""
    
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_PAT')
        self.groq_api_key = os.environ.get('GROQ_API_KEY')
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
    
    def fetch_repo_data(self, repo_url: str) -> Dict[str, Any]:
        """
        Fetch comprehensive repository data from GitHub API
        """
        # Parse owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
        
        owner = parts[-2]
        repo = parts[-1]
        
        # Fetch repository data
        api_url = f'https://api.github.com/repos/{owner}/{repo}'
        response = requests.get(api_url, headers=self.headers)
        
        if response.status_code == 404:
            raise ValueError("Repository not found or is private")
        elif response.status_code != 200:
            raise ValueError(f"GitHub API error: {response.status_code}")
        
        repo_data = response.json()
        
        # Fetch additional data
        languages_url = repo_data.get('languages_url')
        languages = {}
        if languages_url:
            lang_response = requests.get(languages_url, headers=self.headers)
            if lang_response.status_code == 200:
                languages = lang_response.json()
        
        # Fetch contributors
        contributors_url = f'https://api.github.com/repos/{owner}/{repo}/contributors'
        contributors = []
        contrib_response = requests.get(contributors_url, headers=self.headers, params={'per_page': 10})
        if contrib_response.status_code == 200:
            contributors = contrib_response.json()
        
        # Fetch recent commits
        commits_url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        commits = []
        commits_response = requests.get(commits_url, headers=self.headers, params={'per_page': 10})
        if commits_response.status_code == 200:
            commits = commits_response.json()
        
        # Fetch README
        readme_url = f'https://api.github.com/repos/{owner}/{repo}/readme'
        readme_content = ""
        readme_response = requests.get(readme_url, headers=self.headers)
        if readme_response.status_code == 200:
            import base64
            readme_data = readme_response.json()
            readme_content = base64.b64decode(readme_data.get('content', '')).decode('utf-8', errors='ignore')[:5000]  # First 5000 chars
        
        # Fetch directory structure
        tree_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/{repo_data.get("default_branch", "main")}?recursive=1'
        tree_data = []
        tree_response = requests.get(tree_url, headers=self.headers)
        if tree_response.status_code == 200:
            tree_data = tree_response.json().get('tree', [])[:100]  # First 100 files
        
        return {
            'repo': repo_data,
            'languages': languages,
            'contributors': contributors[:10],
            'commits': commits[:10],
            'readme': readme_content,
            'tree': tree_data,
            'owner': owner,
            'repo_name': repo
        }
    
    def generate_ai_analysis(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate AI-powered analysis using Groq Llama 3.3 70B
        """
        if not self.groq_client:
            return {
                'project_purpose': 'AI analysis unavailable - Groq API key not configured',
                'tech_stack': 'Not analyzed',
                'code_structure': 'Not analyzed',
                'architecture': 'Not analyzed',
                'best_practices': 'Not analyzed'
            }
        
        repo = data['repo']
        languages = data['languages']
        readme = data['readme'][:3000]  # Limit for token efficiency
        
        # Build context for AI
        context = f"""
Repository: {repo.get('full_name')}
Description: {repo.get('description', 'No description')}
Primary Language: {repo.get('language', 'Unknown')}
Languages Used: {', '.join(languages.keys()) if languages else 'Unknown'}
Stars: {repo.get('stargazers_count', 0)}
Forks: {repo.get('forks_count', 0)}
README Preview: {readme[:1500] if readme else 'No README available'}
"""
        
        try:
            # Generate comprehensive analysis
            analysis_prompt = f"""Analyze this GitHub repository and provide a detailed technical report.
Format your response with clear bullet points and bold text for key terms.

{context}

Please provide:
1. PROJECT PURPOSE & USE CASES (2-3 sentences explaining what this project does and who would use it)
2. TECH STACK ANALYSIS (detailed breakdown of technologies, frameworks, and tools used)
3. CODE STRUCTURE & ORGANIZATION (explain the project architecture and folder structure)
4. ARCHITECTURE INSIGHTS (describe the design patterns, architectural decisions, and system design)
5. BEST PRACTICES EVALUATION (assess code quality, documentation, testing, and development practices)

Be specific, technical, and insightful. Focus on actionable information."""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert software architect and code analyst. Provide detailed, technical analysis of repositories. Use Markdown formatting (bolding, bullet points) to structure your response clearly."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            full_analysis = response.choices[0].message.content
            
            # Parse the response into sections
            sections = {
                'project_purpose': '',
                'tech_stack': '',
                'code_structure': '',
                'architecture': '',
                'best_practices': ''
            }
            
            # Simple parsing logic
            lines = full_analysis.split('\n')
            current_section = None
            
            for line in lines:
                line_upper = line.upper()
                if 'PROJECT PURPOSE' in line_upper or 'USE CASE' in line_upper:
                    current_section = 'project_purpose'
                elif 'TECH STACK' in line_upper or 'TECHNOLOG' in line_upper:
                    current_section = 'tech_stack'
                elif 'CODE STRUCTURE' in line_upper or 'ORGANIZATION' in line_upper:
                    current_section = 'code_structure'
                elif 'ARCHITECTURE' in line_upper:
                    current_section = 'architecture'
                elif 'BEST PRACTICE' in line_upper:
                    current_section = 'best_practices'
                elif current_section and line.strip():
                    sections[current_section] += line + '\n'
            
            # If parsing failed, use the full analysis
            if not any(sections.values()):
                sections['project_purpose'] = full_analysis[:500]
                sections['tech_stack'] = full_analysis[500:1000]
                sections['code_structure'] = full_analysis[1000:1500]
                sections['architecture'] = full_analysis[1500:2000]
                sections['best_practices'] = full_analysis[2000:]
            
            return sections
            
        except Exception as e:
            print(f"AI analysis error: {str(e)}")
            return {
                'project_purpose': f'Error generating AI analysis: {str(e)}',
                'tech_stack': 'Analysis unavailable',
                'code_structure': 'Analysis unavailable',
                'architecture': 'Analysis unavailable',
                'best_practices': 'Analysis unavailable'
            }

    def _format_markdown_text(self, text: str, style: ParagraphStyle, bullet_style: ParagraphStyle) -> List[Any]:
        """
        Convert markdown-style text (bold, bullets) to ReportLab flowables
        """
        flowables = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Handle bold text: **text** -> <b>text</b>
            # We use a regex to replace all occurrences
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            
            # Handle bullet points
            if formatted_line.startswith('- ') or formatted_line.startswith('* '):
                # Remove the bullet marker
                content = formatted_line[2:].strip()
                flowables.append(Paragraph(f"• {content}", bullet_style))
            else:
                flowables.append(Paragraph(formatted_line, style))
                
        return flowables
    
    def generate_pdf(self, repo_url: str) -> io.BytesIO:
        """
        Generate enhanced PDF report for a repository
        """
        # Fetch data
        data = self.fetch_repo_data(repo_url)
        repo = data['repo']
        
        # Generate AI analysis
        ai_analysis = self.generate_ai_analysis(data)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Title Style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Heading Style
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        # Normal Text Style
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4b5563'),
            spaceAfter=6,
            leading=14,
            alignment=TA_JUSTIFY
        )
        
        # Bullet Point Style
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=normal_style,
            leftIndent=15,
            firstLineIndent=-15,
            spaceAfter=6
        )
        
        # Title Page
        title = Paragraph(f"<b>{repo.get('name', 'Repository')}</b>", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        subtitle = Paragraph(
            f"Comprehensive Repository Analysis Report<br/>"
            f"<font size=10>AI-Powered Analysis • Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</font>",
            ParagraphStyle('Subtitle', parent=normal_style, alignment=TA_CENTER, textColor=colors.HexColor('#6b7280'))
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 40))
        
        # === AI-POWERED SECTIONS ===
        
        # Project Purpose & Use Cases
        elements.append(Paragraph("<b>🎯 Project Purpose & Use Cases</b>", heading_style))
        purpose_text = ai_analysis.get('project_purpose', 'Not available')
        elements.extend(self._format_markdown_text(purpose_text, normal_style, bullet_style))
        elements.append(Spacer(1, 15))
        
        # Tech Stack Analysis
        elements.append(Paragraph("<b>🛠️ Technology Stack Analysis</b>", heading_style))
        tech_text = ai_analysis.get('tech_stack', 'Not available')
        elements.extend(self._format_markdown_text(tech_text, normal_style, bullet_style))
        elements.append(Spacer(1, 15))
        
        # Code Structure
        elements.append(Paragraph("<b>📁 Code Structure & Organization</b>", heading_style))
        structure_text = ai_analysis.get('code_structure', 'Not available')
        elements.extend(self._format_markdown_text(structure_text, normal_style, bullet_style))
        elements.append(Spacer(1, 15))
        
        # Architecture Insights
        elements.append(Paragraph("<b>🏗️ Architecture & Design Patterns</b>", heading_style))
        arch_text = ai_analysis.get('architecture', 'Not available')
        elements.extend(self._format_markdown_text(arch_text, normal_style, bullet_style))
        elements.append(Spacer(1, 15))
        
        # Best Practices
        elements.append(Paragraph("<b>✅ Best Practices Evaluation</b>", heading_style))
        practices_text = ai_analysis.get('best_practices', 'Not available')
        elements.extend(self._format_markdown_text(practices_text, normal_style, bullet_style))
        elements.append(Spacer(1, 30))
        
        # Page Break
        elements.append(PageBreak())
        
        # === REPOSITORY DATA SECTIONS ===
        
        # Repository Overview
        elements.append(Paragraph("<b>📊 Repository Overview</b>", heading_style))
        
        # Safe get functions to handle None values
        def safe_get(value, default='N/A', max_len=None):
            """Safely get a value with optional length limit"""
            if value is None:
                return default
            result = str(value)
            if max_len and len(result) > max_len:
                return result[:max_len] + '...'
            return result
        
        def safe_get_nested(obj, key, nested_key, default='N/A'):
            """Safely get nested dictionary value"""
            nested = obj.get(key)
            if nested is None or not isinstance(nested, dict):
                return default
            return nested.get(nested_key, default) or default
        
        overview_data = [
            ['Owner', safe_get_nested(repo, 'owner', 'login', 'N/A')],
            ['Full Name', safe_get(repo.get('full_name'), 'N/A')],
            ['Description', safe_get(repo.get('description'), 'No description provided', 100)],
            ['Created', datetime.strptime(repo.get('created_at', ''), '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y') if repo.get('created_at') else 'N/A'],
            ['Last Updated', datetime.strptime(repo.get('updated_at', ''), '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y') if repo.get('updated_at') else 'N/A'],
            ['Default Branch', safe_get(repo.get('default_branch'), 'main')],
            ['License', safe_get_nested(repo, 'license', 'name', 'No license')],
            ['Homepage', safe_get(repo.get('homepage'), 'None', 50)],
        ]
        
        overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb'))
        ]))
        elements.append(overview_table)
        elements.append(Spacer(1, 20))
        
        # Statistics
        elements.append(Paragraph("<b>📈 Repository Statistics</b>", heading_style))
        
        stats_data = [
            ['⭐ Stars', str(repo.get('stargazers_count', 0))],
            ['👁 Watchers', str(repo.get('watchers_count', 0))],
            ['🔱 Forks', str(repo.get('forks_count', 0))],
            ['📝 Open Issues', str(repo.get('open_issues_count', 0))],
            ['📦 Size', f"{repo.get('size', 0)} KB"],
            ['🌐 Network Count', str(repo.get('network_count', 0))],
            ['👥 Subscribers', str(repo.get('subscribers_count', 0))],
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 4*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecfdf5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1fae5'))
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Languages
        if data['languages']:
            elements.append(Paragraph("<b>💻 Programming Languages</b>", heading_style))
            
            total_bytes = sum(data['languages'].values())
            lang_data = [['Language', 'Percentage', 'Bytes']]
            
            for lang, bytes_count in sorted(data['languages'].items(), key=lambda x: x[1], reverse=True):
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                lang_data.append([lang, f"{percentage:.1f}%", f"{bytes_count:,}"])
            
            lang_table = Table(lang_data, colWidths=[2*inch, 2*inch, 2*inch])
            lang_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
            ]))
            elements.append(lang_table)
            elements.append(Spacer(1, 20))
        
        # Top Contributors
        if data['contributors']:
            elements.append(Paragraph("<b>👥 Top Contributors</b>", heading_style))
            
            contrib_data = [['Username', 'Contributions', 'Profile']]
            for contrib in data['contributors'][:10]:
                contrib_data.append([
                    contrib.get('login', 'Unknown'),
                    str(contrib.get('contributions', 0)),
                    contrib.get('html_url', '')[:40]
                ])
            
            contrib_table = Table(contrib_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
            contrib_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
            ]))
            elements.append(contrib_table)
            elements.append(Spacer(1, 20))
        
        # Recent Commits
        if data['commits']:
            elements.append(Paragraph("<b>📝 Recent Commits</b>", heading_style))
            
            for commit in data['commits'][:8]:
                commit_msg = commit.get('commit', {}).get('message', 'No message').split('\n')[0]
                author = commit.get('commit', {}).get('author', {}).get('name', 'Unknown')
                date = commit.get('commit', {}).get('author', {}).get('date', '')
                sha = commit.get('sha', '')[:7]
                
                if date:
                    try:
                        date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
                        date = date_obj.strftime('%b %d, %Y')
                    except:
                        pass
                
                commit_text = f"<b>[{sha}]</b> {commit_msg[:70]}<br/><font size=8 color='#6b7280'>by {author} on {date}</font>"
                elements.append(Paragraph(commit_text, normal_style))
                elements.append(Spacer(1, 6))
        
        # Footer
        elements.append(Spacer(1, 30))
        footer_text = f"<font size=8 color='#9ca3af'>AI-Powered Report generated by GitHub Bot • Powered by Llama 3.3 70B • {datetime.now().strftime('%Y')}</font>"
        elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER)))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF value
        buffer.seek(0)
        return buffer


def generate_repo_report(repo_url: str) -> io.BytesIO:
    """
    Generate an enhanced repository report PDF with AI analysis
    """
    generator = EnhancedReportGenerator()
    return generator.generate_pdf(repo_url)
