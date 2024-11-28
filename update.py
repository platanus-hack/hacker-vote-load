import os
import json
from typing import Dict, Any
import psycopg
from datetime import datetime, timezone
from gen_csv import (
    get_branches,
    get_file_content,
    parse_jsonc,
    convert_relative_urls,
    create_slug,
    GITHUB_REPO_BASE_URL,
)

def get_project_data(project_id: int, video_url: str, timestamp_seconds: int, track: str) -> Dict[str, Any]:
    """Process a single project and return its data"""
    print(f"Processing project {project_id}...")

    # Get all branches for the repository
    try:
        branches = get_branches(project_id)
    except Exception as e:
        print(f"Error getting branches for project {project_id}: {e}")
        return None

    description = None
    hack_project = None
    current_branch = None

    # Search for the required files in all branches
    for branch in branches:
        if not description:
            description = get_file_content(project_id, branch, "vote-description.md")
            if description:
                current_branch = branch
        if not hack_project:
            hack_project_content = get_file_content(project_id, branch, "hack-project.jsonc")
            if hack_project_content:
                hack_project = parse_jsonc(hack_project_content)

        # Break loop if both files are found
        if description and hack_project:
            break

    # Skip if no hack project found
    if not hack_project:
        print(f"No hack-project.jsonc found for project {project_id}, skipping...")
        return None

    # Initialize result with basic data
    result = {
        "project_id": project_id,
        "repo_url": GITHUB_REPO_BASE_URL.format(project_id),
        "demo_url": f"{video_url}&t={timestamp_seconds}s",
        "created_at": datetime.now(timezone.utc),
        "track": track
    }
    
    # Update result with description
    if description:
        description = convert_relative_urls(description, project_id, current_branch)
    result["description"] = description or "No description found"
    
    # Update result with hack project data
    project_name = hack_project.get("project_name", "")
    logo_url = hack_project.get("logo_url", "")
    
    # Convert GitHub blob URLs to raw URLs for images
    if logo_url and 'github.com' in logo_url and '/blob/' in logo_url:
        logo_url = logo_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
    
    result.update({
        "project_name": project_name,
        "slug": create_slug(project_name),
        "oneliner": hack_project.get("oneliner", "No oneliner"),
        "logo_url": logo_url or "No logo URL",
        "app_url": hack_project.get("app_url", ""),
    })

    return result

def upsert_project(conn: psycopg.Connection, project_data: Dict[str, Any]):
    """Upsert a project into the database"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO projects (
                project_id, project_name, slug, oneliner, description,
                logo_url, repo_url, app_url, demo_url, track, created_at
            ) VALUES (
                %(project_id)s, %(project_name)s, %(slug)s, %(oneliner)s, %(description)s,
                %(logo_url)s, %(repo_url)s, %(app_url)s, %(demo_url)s, %(track)s, %(created_at)s
            )
            ON CONFLICT (project_id) DO UPDATE SET
                project_name = EXCLUDED.project_name,
                slug = EXCLUDED.slug,
                oneliner = EXCLUDED.oneliner,
                description = EXCLUDED.description,
                logo_url = EXCLUDED.logo_url,
                repo_url = EXCLUDED.repo_url,
                app_url = EXCLUDED.app_url,
                demo_url = EXCLUDED.demo_url,
                track = EXCLUDED.track,
                created_at = EXCLUDED.created_at
        """, project_data)

def main():
    # Get environment variables
    n_projects = int(os.environ["N_PROJECTS"])
    video_url = os.environ["VIDEO_URL"]
    postgres_url = os.environ["POSTGRES_CONN_URL"]
    timestamps = json.loads(os.environ["PROJECTS_TIMESTAMPS"])
    tracks = json.loads(os.environ["PROJECTS_TRACKS"])

    # Connect to PostgreSQL
    with psycopg.connect(postgres_url) as conn:
        # Process each project
        for project_id in range(1, n_projects + 1):
            try:
                # Get timestamp for this project
                timestamp = timestamps.get(str(project_id))
                if timestamp is None:
                    print(f"Warning: No timestamp found for project {project_id}")
                    continue

                # Get track for this project
                track = tracks.get(str(project_id))
                if track is None:
                    print(f"Warning: No track found for project {project_id}")
                    track = "Unspecified"

                # Get project data
                project_data = get_project_data(project_id, video_url, timestamp, track)
                
                # Skip if no data returned
                if project_data is None:
                    continue
                
                # Upsert into database
                upsert_project(conn, project_data)
                conn.commit()
                
                print(f"Successfully processed project {project_id}")
                
            except Exception as e:
                conn.rollback()
                print(f"Error processing project {project_id}: {e}")

if __name__ == "__main__":
    main()
