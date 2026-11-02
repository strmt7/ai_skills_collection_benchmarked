# Attribution and scope

This repair adapts the npm caching guidance in
[Akin Ozer's GitHub Actions generator](https://github.com/akin-ozer/cc-devops-skills/tree/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/github-actions-generator),
licensed under Apache-2.0. The upstream license, original entrypoint and
original composite action are retained in this package. The catalog mirror is
unchanged.

The maintained example always runs `npm ci` after restoring the npm package
cache. It does not repair or qualify the source action's Yarn and pnpm paths or
other generator features. The accompanying controls do not establish an
agent-performance improvement.
