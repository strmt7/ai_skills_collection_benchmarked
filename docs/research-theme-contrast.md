# Theme showcase contrast review

The pinned [theme-factory skill](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/theme-factory/SKILL.md)
asks users to choose a theme from its showcase. We measured the named sample
header and first sample body-text placement on each of its ten pages. Seven of
the ten body samples fall below 4.5:1, and one header falls below 3:1.

| Theme | Header contrast | Body contrast |
| --- | ---: | ---: |
| Ocean Depths | 14.769:1 | 3.795:1 |
| Sunset Boulevard | 3.259:1 | 4.890:1 |
| Forest Canopy | 9.382:1 | 3.686:1 |
| Modern Minimalist | 9.901:1 | 4.055:1 |
| Golden Hour | 5.045:1 | 2.580:1 |
| Arctic Frost | 1.239:1 | 4.897:1 |
| Desert Rose | 5.001:1 | 3.184:1 |
| Tech Innovation | 4.834:1 | 1.254:1 |
| Botanical Garden | 4.382:1 | 1.802:1 |
| Midnight Galaxy | 12.565:1 | 6.143:1 |

For comparison, [W3C's WCAG 2.2 explanation](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum)
uses 4.5:1 for ordinary text and 3:1 for large text, subject to its stated
exceptions. The examined body text is 12 points and the headers are 28 points.
Measure the actual text and background colors in the artifact being produced;
a theme palette alone does not guarantee readable combinations.

The [control](../artifacts/research/2026-10-30/theme-showcase-contrast/reproduce.py)
extracts the page-sized background, named text colors, font sizes and transforms
from the PDF content stream. It calculates the W3C relative-luminance ratio and
checks black-on-white and identical-color reference cases. The calculation
assumes PDF DeviceRGB values are sRGB. [Windows](../artifacts/research/2026-10-30/theme-showcase-contrast/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/theme-showcase-contrast/linux-result.json)
controls used pypdf 6.21.4 and returned the same results. Run with that version
in an isolated Python environment:

```text
python artifacts/research/2026-10-30/theme-showcase-contrast/reproduce.py
```

## Definition consistency

A separate [control](../artifacts/research/2026-10-30/theme-showcase-contrast/check-parity.py)
matched all ten theme definitions to their showcase pages. The four color
labels and both font labels on each page agree with the corresponding
definition, and the two sampled text placements use matching PDF font-resource
names. [Windows](../artifacts/research/2026-10-30/theme-showcase-contrast/parity-windows.json)
and [Linux](../artifacts/research/2026-10-30/theme-showcase-contrast/parity-linux.json)
results agree. Isolated controls with a changed color or font were rejected.
This consistency check does not make the low-contrast samples readable or
verify that these fonts are installed on a user's machine.

GitHub's contents API returned the same showcase blob
`24495d145c95917aba3a3445f7105444b6f7cfcc` at the pinned commit and
[inspected upstream main commit](https://github.com/anthropics/skills/blob/ca45fc496a3436251f191354091d557da31c15b5/skills/theme-factory/theme-showcase.pdf).
Its SHA-256 is `3e126eca9fe99088051f7cb984c97cedb31c7d9e09ce0ba5d61bd01e70a0d253`.
This comparison does not cover the other theme resources.

The W3C page was captured on 30 October 2026 using Crawl4AI
`0.9.5+catalog.portable4` (HTTP 200; native result SHA-256
`bcf9157e783bc28c873e01870e234a48b6c3be057ba6ace81d40a6dc6977b41f`).
This review covers the named samples, not every text placement, a complete
accessibility assessment, full skill evaluation or agent benchmark. The source
mirror is unchanged.
