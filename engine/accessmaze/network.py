"""Explicit origin permissions and a fixed DNS snapshot for each browser lifetime."""

import asyncio
import ipaddress
import socket
from collections import Counter
from urllib.parse import urljoin, urlsplit


def canonical_origin(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(c.isspace() for c in url)
    ):
        raise ValueError("Only HTTP(S) origins without credentials are supported")
    host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    # Resolver rules are command arguments, never shell commands; reject their grammar too.
    if any(c in host for c in ",* /\\\x00"):
        raise ValueError("Invalid origin hostname")
    port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
    if not 1 <= port <= 65535:
        raise ValueError("Invalid origin port")
    authority = f"[{host}]" if ":" in host else host
    default = 443 if parsed.scheme == "https" else 80
    return f"{parsed.scheme}://{authority}" + (f":{port}" if port != default else "")


def resolve_host(url, allow_local):
    parsed = urlsplit(canonical_origin(url))
    addresses = {
        ipaddress.ip_address(item[4][0])
        for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    }
    if not addresses or (not allow_local and any(not ip.is_global for ip in addresses)):
        raise ValueError(
            "Private, loopback and reserved networks require local-network authorization"
        )
    return sorted(addresses, key=lambda ip: (ip.version, int(ip)))


class BrowserPolicy:
    def __init__(self, journey, target, blocked):
        self.journey = journey
        self.target = target
        self.blocked = blocked
        self.navigation = {canonical_origin(target), *journey.network.navigation_origins}
        self.resources = self.navigation | set(journey.network.resource_origins)
        self.effects = False
        self.resolver_rules = []
        self.local_origins = set()
        self.authorized_writes = Counter()

    async def prepare(self):
        allow_local = self.journey.allow_local or self.journey.target.startswith("fixture://")
        hosts = {}
        for url in sorted(self.resources):
            host = urlsplit(url).hostname
            # Fixture authorization covers its own ephemeral server, not added private origins.
            local = (
                allow_local if url == canonical_origin(self.target) else self.journey.allow_local
            )
            addresses = await asyncio.to_thread(resolve_host, url, local)
            if local and all(not address.is_global for address in addresses):
                self.local_origins.add(url)
            hosts.setdefault(host, addresses[0])
        self.resolver_rules = [
            f"MAP {host} {'[' + str(ip) + ']' if ip.version == 6 else ip}"
            for host, ip in hosts.items()
            if not _literal_ip(host)
        ]

    @property
    def launch_args(self):
        args = [
            "--no-proxy-server",
            "--disable-background-networking",
            "--dns-prefetch-disable",
            "--disable-quic",
            "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
        ]
        if self.resolver_rules:
            args.append("--host-resolver-rules=" + ", ".join(self.resolver_rules))
        return args

    async def install(self, context):
        context._accessmaze_policy = self

        async def deny_other_pages(route):
            self.blocked.add("Popup or unattached page request blocked")
            await route.abort("blockedbyclient")

        await context.route("**/*", deny_other_pages)

        async def close_socket(socket):
            self.blocked.add("WebSocket connection blocked")
            await socket.close()

        await context.route_web_socket("**/*", close_socket)

    async def attach(self, page):
        # Page routing overrides the context's default-deny rule. Popups cannot race
        # response-interceptor installation and do not inherit this permission.
        await page.route("**/*", self.route)
        session = await page.context.new_cdp_session(page)
        await session.send(
            "Fetch.enable",
            {"patterns": [{"urlPattern": "*", "requestStage": "Response"}]},
        )

        async def check_response(event):
            headers = {h["name"].lower(): h["value"] for h in event.get("responseHeaders", [])}
            location = headers.get("location")
            reject = False
            method = event["request"]["method"]
            request_url = event["request"]["url"]
            key = (method, request_url)
            write_authorized = self.authorized_writes[key] > 0
            if write_authorized:
                self.authorized_writes[key] -= 1
                if not self.authorized_writes[key]:
                    del self.authorized_writes[key]
            if location and 300 <= event.get("responseStatusCode", 0) < 400:
                status = event["responseStatusCode"]
                redirected_url = urljoin(request_url, location)
                try:
                    destination = canonical_origin(redirected_url)
                except ValueError:
                    destination = None
                permitted = (
                    self.navigation if event.get("resourceType") == "Document" else self.resources
                )
                preserves_method = status in {307, 308} or status in {301, 302} and method != "POST"
                redirected_write = preserves_method and method not in {"GET", "HEAD", "OPTIONS"}
                reject = destination not in permitted or (
                    redirected_write
                    and (not write_authorized or destination not in self.navigation)
                )
                if redirected_write and not reject:
                    # Preserve authorization for this already approved redirect chain,
                    # even if its server response outlives the action window.
                    self.authorized_writes[(method, redirected_url)] += 1
                if reject:
                    self.blocked.add("Cross-origin request blocked")
            command = {"requestId": event["requestId"]}
            if reject:
                command["errorReason"] = "BlockedByClient"
            try:
                await session.send(
                    "Fetch.failRequest" if reject else "Fetch.continueResponse", command
                )
            except Exception:
                if not page.is_closed():
                    self.blocked.add("Response policy failed; page closed")
                    await page.close()

        session.on("Fetch.requestPaused", check_response)

    async def route(self, route):
        request = route.request
        if request.is_navigation_request() and request.frame.parent_frame is not None:
            self.blocked.add("Embedded frame navigation blocked")
            await route.abort("blockedbyclient")
            return
        try:
            allowed = canonical_origin(request.url)
        except ValueError:
            allowed = None
        if allowed not in self.resources or (
            request.is_navigation_request() and allowed not in self.navigation
        ):
            self.blocked.add("Cross-origin request blocked")
            await route.abort("blockedbyclient")
            return
        if request.method not in {"GET", "HEAD", "OPTIONS"} and (
            not self.effects or allowed not in self.navigation
        ):
            self.blocked.add("State-changing request blocked")
            await route.abort("blockedbyclient")
            return
        if self.journey.profile.network_latency_ms:
            await asyncio.sleep(self.journey.profile.network_latency_ms / 1000)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            self.authorized_writes[(request.method, request.url)] += 1
        await route.continue_()


def _literal_ip(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False
