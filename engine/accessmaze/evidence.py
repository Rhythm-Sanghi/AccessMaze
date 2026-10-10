import hashlib
import hmac
import json
import secrets as random_secrets
from urllib.parse import urlsplit, urlunsplit

from playwright.async_api import Error as BrowserError


def safe_url(url):
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc.split("@")[-1], parsed.path, "", ""))


def redact(value, secrets):
    if isinstance(value, str):
        if value == "[redacted]":
            return value
        for secret in sorted(set(secrets), key=len, reverse=True):
            if secret:
                value = value.replace(secret, "[redacted]")
        return value
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, dict):
        metadata = {
            "id",
            "project_id",
            "step_id",
            "blocked_step_id",
            "state_id",
            "source",
            "target",
            "status",
            "action",
            "role",
            "by",
            "rule",
            "severity",
            "verification",
            "first_step",
            "value_from",
            "input_signature",
        }
        return {
            key: item
            if key in metadata and not isinstance(item, (dict, list))
            else redact(item, secrets)
            for key, item in value.items()
        }
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


class EvidencePrivacy:
    def __init__(self, journey, secrets):
        self.secrets = secrets
        self.hide_text = (
            not journey.target.startswith("fixture://") and not journey.privacy.capture_page_text
        )
        self.key = random_secrets.token_bytes(32)

    def token(self, value):
        digest = hmac.new(self.key, value.encode(), hashlib.sha256).hexdigest()[:12]
        return f"[private text {digest}]" if value else ""

    async def observe(self, page):
        data = redact(await observe(page), self.secrets)
        if self.hide_text:
            data["title"] = self.token(data["title"])
            data["headings"] = [self.token(s) for s in data["headings"]]
            for control in data["controls"]:
                control["name"] = self.token(control["name"])
            for node in data.get("ax_tree", {}).get("nodes", []):
                node["name"] = self.token(node["name"])
            parsed = urlsplit(data["url"])
            data["url"] = urlunsplit(
                (parsed.scheme, parsed.netloc, "/" + self.token(parsed.path), "", "")
            )
            data["text_withheld"] = True
        return data

    def interaction(self, data):
        data = redact(data, self.secrets)
        if self.hide_text:
            for focus in data.get("focus_history", []):
                focus["name"] = self.token(focus.get("name", ""))
        return data


async def accessibility_tree(page):
    session = await page.context.new_cdp_session(page)
    try:
        tree = await session.send("Accessibility.getFullAXTree", {"depth": 8})
        nodes = []
        for node in tree["nodes"]:
            role = node.get("role", {}).get("value", "")
            if node.get("ignored") or role in {"StaticText", "InlineTextBox", "generic", "none"}:
                continue
            nodes.append(
                {
                    "role": role,
                    "name": str(node.get("name", {}).get("value", ""))[:200],
                    "focused": any(
                        p["name"] == "focused" and p.get("value", {}).get("value") is True
                        for p in node.get("properties", [])
                    ),
                }
            )
            if len(nodes) >= 500:
                break
        return {
            "source": "Chromium computed accessibility tree",
            "max_depth": 8,
            "max_nodes": 500,
            "nodes": nodes,
        }
    except BrowserError:
        return {"source": "unavailable", "nodes": []}
    finally:
        await session.detach()


async def observe(page):
    data = await page.evaluate("""() => {
      const controls = [...document.querySelectorAll(
        'button,input,select,textarea,a[href],[role=button],[role=dialog],[role=alert],[role=status]'
      )].slice(0,200).map(e=>({
        tag:e.tagName.toLowerCase(), role:e.getAttribute('role'),
        name:((e.getAttribute('aria-labelledby')||'').split(/\\s+/)
          .map(id=>document.getElementById(id)?.textContent||'').join(' ').trim() ||
          e.getAttribute('aria-label') ||
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
    data["ax_tree"] = await accessibility_tree(page)
    return data
