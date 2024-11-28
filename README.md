# Projects Updater

We don´t need a ui for updating a webpage when are users are devs. We just need repos and a script. This is the script part

## Environment Variables

The following environment variables need to be set in GitHub repository settings:

### Secrets
- `POSTGRES_CONN_URL`: PostgreSQL connection URL (format: `postgresql://user:password@host:port/dbname`)

### Variables
- `N_PROJECTS`: Number of projects to process (e.g., `28`)
- `VIDEO_URL`: Base URL for the demo video (e.g., `https://www.youtube.com/watch?v=gnNjc2kxx1E`)
- `PROJECTS_TIMESTAMPS`: JSON mapping of project IDs to video timestamps in seconds  ```json
  {
    "1": 11641,
    "2": 7287,
    ...
  }  ```
- `PROJECTS_TRACKS`: JSON mapping of project IDs to tracks  ```json
  {
    "1": "Health",
    "2": "Tech",
    "3": "Education",
    ...
  }  ```

## Local Development

1. Clone the repository
2. Install dependencies:   ```bash
   pip install -r requirements.txt   ```
3. Set environment variables:   ```bash
   export N_PROJECTS=28
   export VIDEO_URL="https://www.youtube.com/watch?v=gnNjc2kxx1E"
   export POSTGRES_CONN_URL="postgresql://user:password@localhost:5432/dbname"
   export PROJECTS_TIMESTAMPS='{"1": 11641, "2": 7287, ...}'
   export PROJECTS_TRACKS='{"1": "Health", "2": "Tech", ...}'   ```
4. Run the script:   ```bash
   python update.py   ```

## GitHub Actions

The script runs automatically every 15 minutes via GitHub Actions. You can also trigger it manually from the Actions tab in the repository.

To set up:

1. Go to your repository settings
2. Under "Secrets and variables" > "Actions":
   - Add the `POSTGRES_CONN_URL` as a secret
   - Add `N_PROJECTS`, `VIDEO_URL`, `PROJECTS_TIMESTAMPS`, and `PROJECTS_TRACKS` as variables
3. The action will start running automatically according to the schedule 