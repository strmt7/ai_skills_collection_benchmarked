# Stargazer

![stargazer](https://github.com/user-attachments/assets/54d6b003-2f2c-42bd-a8f9-b4e835338dfc)

Stargazer is a GitHub star scraper that collects detailed information about users who star a specific repository. It scrapes data like their emails, usernames, names, company names, locations, and social links. While it grabs a full profile, it is primarily designed to find and verify user emails.

It outperforms standard scrapers by implementing a multi-tier verification system that filters out false positives, specifically those originating from repository forks (e.g., stopping the scraper from accidentally pulling a famous developer's email just because a user forked their repository).

https://github.com/user-attachments/assets/1e15a51b-8bff-4282-928e-fc99da2343cb

## The 5-Tier Extraction Architecture

This system uses five distinct methods to find and verify user emails, ensuring maximum coverage and accuracy:

1. **Profile API**: Direct extraction from the public GitHub user profile.
2. **Events API**: Analysis of recent user activity and public event streams to find associated email addresses.
3. **GPG Keys**: Extraction of email identities linked to verified GPG keys on the user account.
4. **Patch Regex**: Deep scanning of commit patches and diffs using regular expressions to identify author emails.
5. **Global Search API**: Advanced search queries with cryptographic login verification to find user mentions across the platform.

## Key Features

*   **Multi-Token Rotation**: Supports a pool of GitHub Personal Access Tokens to distribute requests and maximize speed.
*   **Smart Rate Limiting**: Uses semaphores to manage concurrency and bypass the standard 30 requests per minute search limit safely.
*   **JSONL Checkpointing**: Saves progress in real-time using JSON Lines format, allowing for easy resumption if your internet drops or the script is stopped.
*   **Jitter**: Implements randomized delays between requests to mimic human behavior and avoid GitHub abuse detection.
*   **CSV Generation**: Includes built-in tools to transform raw extraction data into clean, structured CSV files for marketing or analysis.

## How to get a GitHub Personal Access Token (PAT)

To run the scraper, you will need at least one GitHub Personal Access Token (though 3 or more are recommended for repositories with thousands of stars).

1. Go to your GitHub Token Settings: https://github.com/settings/tokens
2. Click **Generate new token (classic)**.
3. Give it a descriptive note (e.g., "Stargazer Scraper").
4. Under scopes, select **`read:user`** and **`user:email`**. This allows the script to read public profile data and emails. No other permissions are required.
5. Scroll down and click **Generate token**.
6. Copy the `<GITHUB_TOKEN>` string and paste it into your `.env` file.

## Installation

1. Clone the repository to your local machine.
2. Install the required dependencies using pip:
   ```bash
   pip install aiohttp python-dotenv
   ```
3. Create a `.env` file in the root directory. You can use `stargazer-skill/assets/.env.example` as a template.

## Configuration

Edit the `.env` file with your specific settings:

*   `GITHUB_PATS`: A comma-separated list of your GitHub Personal Access Tokens.
*   `TARGET_OWNER`: The username or organization that owns the repository.
*   `TARGET_REPO`: The name of the repository to scan.
*   `MAX_USERS`: The maximum number of stargazers to process.
*   `MAX_CONCURRENT`: The number of concurrent requests to run (50 is recommended).

## Usage Guide

Run the extraction process in three sequential steps.

### 1. Extract Data
Start the main extraction script to gather detailed user information.
```bash
python stargazer-skill/scripts/stargazer_deep_extractor.py
```

### 2. Count Results
Analyze the extracted data to see how many unique emails were found. You can run this while the main script is running.
```bash
python stargazer-skill/scripts/count_emails.py
```

### 3. Convert to CSV
Generate a final CSV file for use in other applications.
```bash
python stargazer-skill/scripts/convert_to_csv.py
```
