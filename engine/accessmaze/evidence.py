import hashlib
import json
from urllib.parse import urlsplit, urlunsplit


def safe_url(url):
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc.split("@")[-1], parsed.path, "", ""))


def redact(value, secrets):
    if isinstance(value, str):
        for secret in sorted(set(secrets), key=len, reverse=True):
            if secret:
                value = value.replace(secret, "[redacted]")
        return value
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, dict):
        return {key: redact(item, secrets) for key, item in value.items()}
    return value


def public_journey(journey):
    data = journey.model_dump()
    for step in data["steps"]:
        if step["action"] in {"fill", "assert_value"}:
            step["value"] = "[redacted]"
    return data


def fingerprint(observation):
    stable = {key: value for key, value in observation.items() if key != "timestamp"}
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()[:16]


async def observe(page):
    data = await page.evaluate("""() => {
      const controls = [...document.querySelectorAll(
        'button,input,select,textarea,a[href],[role=button],[role=dialog],[role=alert],[role=status]'
      )].slice(0,200).map(e=>({
        tag:e.tagName.toLowerCase(), role:e.getAttribute('role'),
        name:(e.getAttribute('aria-label') ||
          (e.labels ? [...e.labels].map(l=>l.textContent).join(' ') : '')
          || (['BUTTON','A'].includes(e.tagName) || e.hasAttribute('role') ? e.textContent : '')
          || '').trim().slice(0,160),
        disabled:e.matches(':disabled'), visible:!!e.getClientRects().length,
        invalid:e.getAttribute('aria-invalid'), populated:!!e.value,
        focused:e===document.activeElement
      }));
      return {title:document.title.slice(0,160),controls,
        headings:[...document.querySelectorAll('h1,h2,h3')].slice(0,30)
          .map(e=>e.textContent.trim().slice(0,160)),
        online:navigator.onLine,
        reduced_motion:matchMedia('(prefers-reduced-motion: reduce)').matches};
    }""")
    data["url"] = safe_url(page.url)
    return data
