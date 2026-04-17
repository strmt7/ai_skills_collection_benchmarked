# YC Intent Radar

<img width="1280" height="640" alt="yc-intent-radar-cover" src="https://github.com/user-attachments/assets/2328ae2b-1b5d-45ad-8604-b90721b8d398" />

An automated scraper that pulls job listings and company data from YCombinator's Workatastartup platform. It bypasses login bottlenecks by utilizing authenticated sessions and ensures no duplicates are recorded by saving everything directly to a local SQLite database (`jobs.db`).

## Features
- **Deduplication:** Utilizes `better-sqlite3` to store state, ensuring you never scrape the same job twice.
- **Robust Extraction:** Identifies hidden JSON payloads on YC pages to grab accurate backend `job_id` values.
- **Filtered Exports:** Includes an export script (`export_radar_candidates.js`) that queries the SQLite database for intent-based hiring (e.g., GTM, DevRel, Growth, Content) and outputs it as a JSON payload for secondary research tools.

## Setup
1. Clone the repository.
2. Navigate to the `scripts/` directory:
   ```bash
   cd scripts
   npm install
   npx playwright install
   ```

3. **Authenticate (First Time Only):**
   Run the following script and log in to YC via the browser that opens. This creates a `state.json` file.
   ```bash
   node auth.js
   ```

4. **Run the Scraper:**
   ```bash
   node scraper.js
   ```

5. **Export Targeted Jobs:**
   ```bash
   node export_radar_candidates.js
   ```
   This will query the DB and produce `radar_candidates.json` containing the targeted companies and matching roles.

## Note on Sensitive Files
The `.gitignore` strictly protects your `state.json` (authentication cookies) and `jobs.db` (local history). Do not commit these files to a public repository.
