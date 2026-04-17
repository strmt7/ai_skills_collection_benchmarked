# Security

Do not commit credentials or provider-shaped example credentials.

Use neutral placeholders such as `<GOOGLE_API_KEY>`, `<AWS_ACCESS_KEY_ID>`, `<OPENAI_API_KEY>`, or `<TOKEN>` in docs and fixtures. Do not use strings that match real provider token formats, even when the value is meant as an example.

Before pushing, run:

```bash
python3 tools/check_no_secret_patterns.py --history
```

GitHub secret scanning and push protection are enabled for this repository. The local scanner is intentionally strict so generated mirrors, examples, fixtures, and documentation fail if they contain secret-shaped values.
