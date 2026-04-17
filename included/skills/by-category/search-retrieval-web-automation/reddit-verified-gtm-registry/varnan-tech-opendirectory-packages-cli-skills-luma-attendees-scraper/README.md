# Luma Attendees Scraper

<img width="1280" height="640" alt="luma-attendees-scraper-cover" src="https://github.com/user-attachments/assets/44acd3d4-8c4d-4c8a-823b-96cd6585e5ae" />

Browser-console script to export attendee data from a Luma event into CSV.

[luma-attendees-scraper.webm](https://github.com/user-attachments/assets/d324ee4a-8006-44ae-9cee-dca414ef03e9)

## Note

For a test run, set:

```js
sampleLimit: 5,
```

This exports a small sample so you can verify the output columns first.

If the sample looks correct, switch to:

```js
sampleLimit: Infinity,
```

This exports all available attendees for the event.

The script:

- works from the browser console
- accepts any Luma event URL
- fetches the event's internal `event_api_id` automatically
- exports attendee data from Luma's paginated guest API
- includes public social handles already present in the guest payload

## Files

- `luma_attendees_export.js`: main browser-console script

## Requirements

- You must be logged into Luma in your browser.
- Your account must have permission to view the event attendee list.
- The script should be run on `luma.com` while your authenticated Luma session is active.

If Luma returns `403` with a message like `You don't have access to this event.`, the problem is account access, not the script.

## How To Use

1. Open the target Luma event page in your browser.
2. Open DevTools Console.
3. If Chrome blocks paste in the console, type `allow pasting` and press Enter.
4. Open `luma_attendees_export.js` from this repo.
5. Edit the `CONFIG` block at the top if needed.
6. Paste the full script into the browser console and run it.
7. Wait for the CSV download.

## Recommended Flow

### 1. Verify on a small sample first

Set:

```js
sampleLimit: 5,
```

This exports only the first 5 attendees and is the safest way to confirm the output columns look right.

### 2. Run the full export

After the sample looks correct, switch to:

```js
sampleLimit: Infinity,
```

This exports the full attendee list.

## Config

The script starts with:

```js
const CONFIG = {
  eventUrl: window.location.href,
  sampleLimit: 5,
  pageSize: 100,
  requestDelayMs: 150,
  apiBase: "https://api2.luma.com",
  outputFileName: "",
};
```

### Config fields

- `eventUrl`: Luma event URL to export. Default is the current page URL.
- `sampleLimit`: number of attendees to export. Use `5` for testing or `Infinity` for all attendees.
- `pageSize`: API page size. `100` is a good default.
- `requestDelayMs`: delay between paginated API requests.
- `apiBase`: Luma API base URL.
- `outputFileName`: optional custom CSV filename. Leave empty to auto-generate one.

## CSV Columns

The export includes:

- `Event Name`
- `Event URL`
- `Event API ID`
- `Section`
- `Name`
- `First Name`
- `Last Name`
- `Bio`
- `Profile URL`
- `Username`
- `API ID`
- `Instagram`
- `X`
- `TikTok`
- `LinkedIn`
- `Website`
- `YouTube`
- `Avatar URL`
- `Verified`
- `Timezone`
- `Last Online At`
- `Tickets Registered`

## Why This Works Better Than DOM Scraping

Many Luma event pages no longer render the full attendee list directly in the page DOM. Older console scripts that scrape `a[href^="/user/"]` only capture whatever is currently visible on the page, which may be one attendee or a very small subset.

This script uses the paginated guest API that Luma itself calls when loading attendee data, so it can export the full list when your account has access.

## Data Trust Model

- Attendee rows are exported from Luma's backend guest response.
- Social fields are read from the guest payload itself when available.
- The script does not invent people, create fake profiles, or synthesize attendee data.
- If a field is missing from Luma's response, the CSV cell is left blank.

## Troubleshooting

### `403 You don't have access to this event.`

Your Luma account cannot access that event's guest list. Use an account that can view the attendees.

### CSV downloads but values are blank

This usually means the guest payload shape has changed. Check the `Sample guest:` object printed in the console and update the field mapping.

### Only a few attendees exported

Make sure `sampleLimit` is not still set to a small number like `5`.

### No download starts

Some browsers block downloads from DevTools-triggered scripts until user interaction is allowed. Re-run after enabling downloads for the site.

## Suggested Usage Pattern

1. Run with `sampleLimit: 5`
2. Inspect the CSV
3. Switch to `sampleLimit: Infinity`
4. Run again for the full export

## Disclaimer

Use this responsibly and only for events and attendee lists your account is authorized to access.
