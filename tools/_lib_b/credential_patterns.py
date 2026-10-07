"""Credential shapes shared by detection and explicitly versioned neutralization.

Primary key semantics: https://docs.stripe.com/keys and
https://docs.stripe.com/webhooks/signature. Publishable keys are not secrets.
Bare prefixes and neutral placeholders remain usable documentation.
"""

import re

STRIPE_SERVER_KEY = re.compile(r"(?<![A-Za-z0-9_-])(?:[sr]k_(?:live|test)_|sk_org_)[A-Za-z0-9.][A-Za-z0-9_.-]*")
STRIPE_WEBHOOK_SECRET = re.compile(r"(?<![A-Za-z0-9_-])whsec_[A-Za-z0-9.][A-Za-z0-9_.-]*")

V2_NEUTRALIZATIONS = (
    (STRIPE_SERVER_KEY, "<STRIPE_SERVER_KEY>"),
    (STRIPE_WEBHOOK_SECRET, "<STRIPE_WEBHOOK_SECRET>"),
)
