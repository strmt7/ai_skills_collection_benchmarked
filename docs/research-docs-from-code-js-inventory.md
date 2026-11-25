# JavaScript and TypeScript documentation inventory

The mirrored TypeScript fallback's observed startup and route-discovery
failures are described in the [component review](research-docs-from-code.md).
The separate [maintained inventory](../included/repaired/skills/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/docs-from-code-js-inventory/SKILL.md)
parses JavaScript and TypeScript source and reports selected Express and
Next.js route candidates. The pinned mirror remains unchanged.

The [qualification](../artifacts/repaired-skill-readiness/docs-from-code-js-inventory-v1/qualification.json)
binds the tested files to Windows and Linux runs on Node 24.22.3 and 26.13.1.
Eight cases include requests to owned Express 5.3.0 and Next.js 16.4.6
fixtures over a local socket or named pipe. A separate clean installation
tests the minimal runtime package and CLI with Babel parser 8.1.3.
These fixtures exercise a small part of each framework. The inventory does
not import the target project, and its output is neither an API contract nor
evidence of improved agent performance.

The [Next.js route-handler convention](https://nextjs.org/docs/app/getting-started/route-handlers)
allows nested `route.js` and `route.ts` handlers; the
[route-group convention](https://nextjs.org/docs/app/api-reference/file-conventions/route-groups)
omits groups from URLs. [Express routing](https://expressjs.com/en/guide/routing/)
uses methods and routers, while [Babel's parser](https://babeljs.io/docs/babel-parser)
supports TypeScript and configurable parsing plugins. Source observations and
capture digests are in the [source record](../artifacts/repaired-skill-readiness/docs-from-code-js-inventory-v1/sources.json).
This scoped repair does not qualify graphify, all routing conventions, or the
full source skill.
