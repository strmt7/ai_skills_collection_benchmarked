---
name: show-hn-writer
description: ''
compatibility: [claude-code, gemini-cli, github-copilot]
author: OpenDirectory
version: 1.0.0
---

# Show HN Writer

Draft a Show HN post title and body that follows the unwritten rules of Hacker News: specific, honest, first-person, no marketing.

---

**Critical rule:** Never use marketing language. No "game-changing", "revolutionary", "powerful", "robust", "seamless", "innovative", "best-in-class", or "streamline". Never write in third person about the product. Never ask readers to upvote, share, or check out other links.

---

## Step 1: Gather Project Context

Check if the user has already provided enough context to write the post. You need:

- What the project does (one technical sentence)
- What problem it solves and who has that problem
- Why the builder made it (the honest story: scratch your own itch, side project, weekend hack)
- What makes it technically interesting or different from existing solutions
- Current state: alpha, beta, open source, free, paid, solo project, team

If any of these are missing, ask in a single message:

"To write your Show HN post, I need a few details:
1. What does [project name] do, technically? (one sentence)
2. Who has the problem it solves? (be specific: 'developers who...' not 'anyone who...')
3. Why did you build it? (the real story)
4. What's technically interesting about how it works?
5. What's the current state: open source? free? alpha?"

Do not proceed until you have answers to all five.

---

## Step 2: Read Context Files (if available)

Check for project context files before asking:

```bash
ls README.md 2>/dev/null && echo "README found"
ls CLAUDE.md 2>/dev/null && echo "CLAUDE.md found"
ls package.json 2>/dev/null && echo "package.json found"
```

If README.md exists, read the first 100 lines. Extract: what it does, tech stack, how to run it, any stated motivation.

If you find enough context in the files, skip the Step 1 questions entirely or ask only what's missing.

---

## Step 3: Draft the Title

The Show HN title must start with "Show HN:": this is required, not optional.

**Title format A: Product-First:**
```
Show HN: [Project Name] – [what it does in plain English]
```

**Title format B: Outcome-Focused:**
```
Show HN: [Project Name] – [specific outcome] for [specific person]
```

**Title rules:**
- 60-80 characters total (including "Show HN: ")
- No exclamation marks
- No adjectives ("fast", "simple", "easy", "powerful") unless they are literal technical specs
- The dash is an en dash (–), not a hyphen (-)
- No trailing punctuation
- Describe what it does, not what it could do for someone

Good examples:
- `Show HN: Zulip – Group chat that threads every conversation`
- `Show HN: Lite XL – A lightweight text editor written in C and Lua`
- `Show HN: Datasette – Instantly publish SQLite databases to the web`

Bad examples (never write these):
- `Show HN: The most powerful tool for managing your workflow` (adjective, no specifics)
- `Show HN: Check out my new project!` (no description, no name)
- `Show HN: I built a thing for developers` (vague)

Draft three title variants:
1. Product-First format
2. Outcome-Focused format
3. Technical-Angle format (lead with the interesting technical decision)

---

## Step 4: Draft the Body

The Show HN body is a builder talking to peers. It is not a product description. It is not a pitch.

**Structure:**

**Opening line:** One sentence, first-person, what you built. Not "Introducing X" or "X is a tool that". Just: "I built [X] because [reason]." or "For the past [N] months I've been working on [X]."

**The why:** Two to four sentences on why you made it. Was it a problem you had personally? Something frustrating at work? A technical curiosity? Be specific and honest. If you built it for fun, say so.

**How it works:** Three to six sentences on the technical approach. This is what HN readers care about. What's the interesting engineering decision? What did you learn? What tradeoff did you make and why? Name the specific technology choices.

**Current state:** One to two sentences. Is it open source? Free? Alpha? Looking for beta users? Solo project or team? How long have you been working on it?

**Invitation:** One sentence to close. Invite feedback, questions, or criticism. Never ask for upvotes or shares. Examples: "Would love to hear what you think." / "Happy to answer questions about the implementation." / "Criticism welcome: still early days."

**Body rules:**
- Write in first person throughout
- 150-350 words total
- No bullet points, no headers, no bold text
- No links in the body (the URL goes in the submission, not the body)
- No asking people to sign up, follow, or subscribe
- No comparison tables or feature lists
- If there's a demo or GitHub link, do NOT add it to the body: it goes in the URL field of the submission

---

## Step 5: Summarize Submission with Gemini

Write a Gemini request to evaluate the draft and check for Show HN anti-patterns:

```bash
cat > /tmp/show-hn-review-request.json << 'ENDJSON'
{
  "system_instruction": {
    "parts": [{
      "text": "You are a longtime Hacker News member reviewing a Show HN post draft. Your job is to catch anything that will hurt its reception: marketing language, vague descriptions, third-person writing, requests for upvotes/shares, adjectives without specifics, titles over 80 characters. For each issue found, state: the exact phrase, why it hurts, and a specific suggested replacement. If the post passes, say 'Passes review.' Output only the review: no commentary, no preamble. Do not use em dashes. Do not praise the post."
    }]
  },
  "contents": [{
    "parts": [{
      "text": "DRAFT_POST_HERE"
    }]
  }],
  "generationConfig": {
    "temperature": 0.2,
    "maxOutputTokens": 1024
  }
}
ENDJSON

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/show-hn-review-request.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['candidates'][0]['content']['parts'][0]['text'])"
```

Replace `DRAFT_POST_HERE` with the full title and body text.

**If GEMINI_API_KEY is not set:** Skip this step. Proceed with the manual self-QA in Step 6.

---

## Step 6: Self-QA

Before presenting the final output, check each item:

**Title checks:**
- [ ] Starts with exactly "Show HN:" (capital H, capital N, colon, space)
- [ ] 60-80 characters total
- [ ] Contains no marketing adjectives
- [ ] Describes what the product does, not what it will do for someone
- [ ] No exclamation marks

**Body checks:**
- [ ] Opens in first person ("I built...", "For the past N months...", "I've been working on...")
- [ ] 150-350 words
- [ ] Contains at least one technical detail (language, approach, architecture decision)
- [ ] No links in the body text
- [ ] Closes with an invitation for feedback, not a call to action
- [ ] No bullet points or headers
- [ ] No marketing words: "game-changer", "revolutionary", "powerful", "robust", "seamless", "innovative", "best-in-class", "streamline", "leverage", "transform"

If any check fails, fix before presenting.

---

## Step 7: Post to Hacker News (Optional)

If `HN_USERNAME` and `HN_PASSWORD` are set in the environment, offer to post directly.

```bash
echo "HN_USERNAME: ${HN_USERNAME:-not set}"
echo "HN_PASSWORD: ${HN_PASSWORD:+set (hidden)}"
```

If both are set, tell the user: "HN credentials found. Confirm to submit this post directly to Hacker News, or say 'output only' to get the text."

On confirmation, run the three-step submission:

**Step A: Authenticate and get session cookie**
```bash
HN_COOKIE=$(curl -s -c /tmp/hn-cookies.txt -b /tmp/hn-cookies.txt \
  -X POST "https://news.ycombinator.com/login" \
  -d "acct=${HN_USERNAME}&pw=${HN_PASSWORD}&goto=news" \
  -D /tmp/hn-headers.txt \
  -L -o /dev/null -w "%{http_code}")

# Verify login succeeded (should redirect to news, not back to login)
grep -c "user?id=${HN_USERNAME}" /tmp/hn-headers.txt > /dev/null 2>&1 \
  || curl -s -b /tmp/hn-cookies.txt "https://news.ycombinator.com/" \
     | grep -c "logout" > /dev/null 2>&1 \
  && echo "Login: success" || echo "Login: failed: check credentials"
```

If login fails: stop. Tell the user their credentials did not work and present the draft for manual submission instead.

**Step B: Fetch the submission form to get the CSRF token (fnid)**
```bash
FNID=$(curl -s -b /tmp/hn-cookies.txt \
  "https://news.ycombinator.com/submit" \
  | python3 -c "
import sys, re
html = sys.stdin.read()
m = re.search(r'name=\"fnid\" value=\"([^\"]+)\"', html)
print(m.group(1) if m else 'NOT_FOUND')
")
echo "fnid: $FNID"
```

If fnid is NOT_FOUND: stop. HN may have changed their form structure. Present the draft for manual submission.

**Step C: Submit the post**

For a URL submission (project URL):
```bash
curl -s -b /tmp/hn-cookies.txt \
  -X POST "https://news.ycombinator.com/r" \
  -d "title={ENCODED_TITLE}&url={ENCODED_URL}&fnid=${FNID}&fnop=submit-page" \
  -D /tmp/hn-submit-headers.txt \
  -L -o /tmp/hn-submit-response.html

# Check for success: HN redirects to the post or to newest
grep -E "item\?id=|/newest" /tmp/hn-submit-headers.txt \
  && echo "Submission: success" || echo "Submission: check manually"
```

For a text post (no URL, just body):
```bash
curl -s -b /tmp/hn-cookies.txt \
  -X POST "https://news.ycombinator.com/r" \
  -d "title={ENCODED_TITLE}&text={ENCODED_BODY}&fnid=${FNID}&fnop=submit-page" \
  -D /tmp/hn-submit-headers.txt \
  -L -o /tmp/hn-submit-response.html
```

**After submission:**
1. Extract the post URL from the redirect headers
2. Tell the user: "Posted: https://news.ycombinator.com/item?id=[ID]"
3. Remind them: "Reply to comments within the first two hours. Do not reshare the link for 24 hours: HN penalizes vote rings."

**If any step fails:** Clean up cookie file (`rm -f /tmp/hn-cookies.txt`) and present the draft for manual submission. Do not retry automatically.

```bash
# Always clean up credentials from disk after the session
rm -f /tmp/hn-cookies.txt /tmp/hn-headers.txt /tmp/hn-submit-headers.txt /tmp/hn-submit-response.html
```

If `HN_USERNAME` or `HN_PASSWORD` is not set: skip this step entirely and proceed to Step 8.

---

## Step 8: Present Output

Present in this order:

```
## Show HN Post

### Recommended Title
Show HN: [title]

### Alternative Titles
1. Show HN: [variant 1]
2. Show HN: [variant 2]

---

### Body

[post body text]

---

### Submission Notes
- URL field: [project URL or GitHub URL]
- Best time to post: Tuesday to Thursday, 8–10 AM US Eastern
- After posting: Respond to every comment in the first two hours
- Do not share the link elsewhere for the first 24 hours: HN flags vote rings
```

Do not add commentary about the post. Present the output, then stop.
