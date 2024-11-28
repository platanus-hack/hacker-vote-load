import requests
import pyjson5 as json5
import re
import unicodedata

# GitHub API setup
GITHUB_API_BASE_URL = "https://api.github.com/repos/platanus-hack/team-{}/branches"
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/platanus-hack/team-{}/"
GITHUB_REPO_BASE_URL = "https://github.com/platanus-hack/team-{}"

def get_branches(project_id):
    """Fetch branch names for a repository"""
    url = GITHUB_API_BASE_URL.format(project_id)
    response = requests.get(url)
    response.raise_for_status()
    return [branch['name'] for branch in response.json()]

def get_file_content(project_id, branch, file_path):
    """Fetch the content of a file from a specific branch"""
    url = f"{GITHUB_RAW_BASE_URL.format(project_id)}{branch}/{file_path}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

def parse_jsonc(jsonc_content):
    """Parse JSONC content using pyjson5"""
    if not jsonc_content:
        return None
    try:
        return json5.loads(jsonc_content)
    except Exception as e:
        print(f"Error parsing JSONC: {e}")
        return None

def convert_relative_urls(content, project_id, branch):
    """Convert relative URLs in markdown content to absolute GitHub URLs"""
    if not content:
        return content
        
    # Base URL for raw content (for images)
    base_raw_url = f"https://raw.githubusercontent.com/platanus-hack/team-{project_id}/{branch}"
    # Base URL for GitHub web interface (for regular links)
    base_github_url = f"https://github.com/platanus-hack/team-{project_id}/blob/{branch}"
    
    # Convert image references ![alt](./path) or ![alt](../path) or ![alt](path)
    content = re.sub(
        r'!\[(.*?)\]\((?!http[s]?://)(\.{0,2}/)?([^)]+)\)',
        rf'![\1]({base_raw_url}/\3)',
        content
    )
    
    # Convert regular markdown links [text](./path) or [text](../path) or [text](path)
    content = re.sub(
        r'\[(.*?)\]\((?!http[s]?://)(\.{0,2}/)?([^)]+)\)',
        rf'[\1]({base_github_url}/\3)',
        content
    )
    
    # Convert HTML img tags with relative src
    def replace_img_src(match):
        full_tag = match.group(0)
        path = match.group(2)
        # Only replace if it's not already an absolute URL
        if not path.startswith(('http://', 'https://')):
            return full_tag.replace(path, f"{base_raw_url}/{path}")
        return full_tag

    content = re.sub(
        r'<img\s+[^>]*?src=["\'](?!http[s]?://)(\.{0,2}/)?([^"\']+)["\'][^>]*>',
        replace_img_src,
        content
    )
    
    # Convert other HTML tags with relative references (href, data-src, etc)
    def replace_href_src(match):
        prefix = match.group(1)
        path = match.group(3)
        suffix = match.group(4)
        
        # Use raw URL for image files, regular GitHub URL for others
        is_image = path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'))
        base_url = base_raw_url if is_image else base_github_url
        
        if not path.startswith(('http://', 'https://')):
            return f"{prefix}{base_url}/{path}{suffix}"
        return f"{prefix}{path}{suffix}"

    content = re.sub(
        r'(<[^>]+?(?:href|src|data-src)=["\'])(?!http[s]?://)(\.{0,2}/)?([^"\']+)(["\'][^>]*>)',
        replace_href_src,
        content
    )
    
    return content

def create_slug(text):
    """Convert text to URL-friendly slug"""
    if not text:
        return ""
    
    # Convert to lowercase and normalize unicode characters
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    
    # Replace any non-alphanumeric character with a dash
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Remove leading/trailing dashes
    text = text.strip('-')
    
    # Collapse multiple dashes into one
    text = re.sub(r'-+', '-', text)
    
    return text
