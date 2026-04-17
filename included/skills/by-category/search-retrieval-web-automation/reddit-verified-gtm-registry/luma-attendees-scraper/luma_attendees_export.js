(async function () {
  const CONFIG = {
    eventUrl: window.location.href,
    sampleLimit: 5,
    pageSize: 100,
    requestDelayMs: 150,
    apiBase: "https://api2.luma.com",
    outputFileName: "",
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  function normalizeHandleUrl(value, baseUrl) {
    if (!value) return "";
    if (/^https?:\/\//i.test(value)) return value;
    if (value.startsWith("/")) return `${baseUrl}${value}`;
    return `${baseUrl}/${value.replace(/^@/, "")}`;
  }

  function getProfileUrl(user) {
    if (!user) return "";
    if (user.profile_url) return user.profile_url;
    if (user.user_url) return user.user_url;
    if (user.url) return user.url;
    if (user.username) return `https://luma.com/user/${user.username}`;
    return "";
  }

  function csvEscape(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function slugify(value) {
    return String(value || "luma-event")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80);
  }

  function extractEventApiId(html) {
    const patterns = [
      /"event_api_id":"(evt-[^"]+)"/,
      /"api_id":"(evt-[^"]+)"/,
      /event_api_id\\":\\"(evt-[^"]+)/,
      /api_id\\":\\"(evt-[^"]+)/,
    ];

    for (const pattern of patterns) {
      const match = html.match(pattern);
      if (match) return match[1];
    }

    throw new Error("Could not find event_api_id in the event page HTML.");
  }

  function extractEventName(html) {
    const titleMatch = html.match(/<title>(.*?)<\/title>/i);
    if (titleMatch) {
      return titleMatch[1]
        .replace(/\s*[|·-]\s*Luma.*$/i, "")
        .replace(/\s+/g, " ")
        .trim();
    }

    const namePatterns = [
      /"name":"([^"]+)"/,
      /"event_name":"([^"]+)"/,
    ];

    for (const pattern of namePatterns) {
      const match = html.match(pattern);
      if (match) return match[1];
    }

    return "luma-event";
  }

  async function fetchJson(url) {
    const response = await fetch(url, {
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Request failed (${response.status}): ${text}`);
    }

    return response.json();
  }

  async function fetchEventContext(eventUrl) {
    const response = await fetch(eventUrl, { credentials: "include" });
    if (!response.ok) {
      throw new Error(`Failed to load event page (${response.status})`);
    }

    const html = await response.text();
    return {
      eventApiId: extractEventApiId(html),
      eventName: extractEventName(html),
      eventUrl,
    };
  }

  async function fetchGuests(eventApiId, limit) {
    const guests = [];
    let cursor = null;

    while (true) {
      const url = new URL(`${CONFIG.apiBase}/event/get-guest-list`);
      url.searchParams.set("event_api_id", eventApiId);
      url.searchParams.set("pagination_limit", String(CONFIG.pageSize));
      if (cursor) url.searchParams.set("pagination_cursor", cursor);

      const data = await fetchJson(url.toString());
      const entries = Array.isArray(data.entries) ? data.entries : [];

      guests.push(...entries);
      console.log(`Fetched ${guests.length} guests so far`);

      if (guests.length >= limit) {
        return guests.slice(0, limit);
      }

      if (!data.has_more || !data.next_cursor) {
        return guests;
      }

      cursor = data.next_cursor;
      await sleep(CONFIG.requestDelayMs);
    }
  }

  function buildRows(eventContext, guests) {
    const rows = [[
      "Event Name",
      "Event URL",
      "Event API ID",
      "Section",
      "Name",
      "First Name",
      "Last Name",
      "Bio",
      "Profile URL",
      "Username",
      "API ID",
      "Instagram",
      "X",
      "TikTok",
      "LinkedIn",
      "Website",
      "YouTube",
      "Avatar URL",
      "Verified",
      "Timezone",
      "Last Online At",
      "Tickets Registered",
    ]];

    for (const guest of guests) {
      const user = guest.user || {};

      rows.push([
        eventContext.eventName,
        eventContext.eventUrl,
        eventContext.eventApiId,
        guest.section_label || "",
        user.name || "",
        user.first_name || "",
        user.last_name || "",
        (user.bio_short || "").replace(/\s+/g, " ").trim(),
        getProfileUrl(user),
        user.username || "",
        user.api_id || guest.api_id || "",
        normalizeHandleUrl(user.instagram_handle, "https://instagram.com"),
        normalizeHandleUrl(user.twitter_handle, "https://x.com"),
        normalizeHandleUrl(user.tiktok_handle, "https://www.tiktok.com/@"),
        normalizeHandleUrl(user.linkedin_handle, "https://www.linkedin.com"),
        user.website || "",
        normalizeHandleUrl(user.youtube_handle, "https://www.youtube.com/@"),
        user.avatar_url || "",
        user.is_verified ? "true" : "false",
        user.timezone || "",
        user.last_online_at || "",
        guest.num_tickets_registered || 0,
      ]);
    }

    return rows;
  }

  function downloadCsv(rows, fileName) {
    const csv = rows.map((row) => row.map(csvEscape).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  }

  const eventContext = await fetchEventContext(CONFIG.eventUrl);
  const limit = Number.isFinite(CONFIG.sampleLimit) ? CONFIG.sampleLimit : Infinity;
  const guests = await fetchGuests(eventContext.eventApiId, limit);
  const rows = buildRows(eventContext, guests);
  const fileName =
    CONFIG.outputFileName ||
    `${slugify(eventContext.eventName)}-${Number.isFinite(limit) ? `sample-${limit}` : "all"}-attendees.csv`;

  console.log("Event context:", eventContext);
  console.log("Guests exported:", guests.length);
  console.log("Sample guest:", guests[0] || null);

  downloadCsv(rows, fileName);
})();
