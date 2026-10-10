"""Owned, real HTTP SPA/API servers. No Playwright routing mocks or external writes."""

import threading
import time
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from accessmaze.models import Journey, Step


class CompatibilityApp:
    def __init__(self):
        self.broken = False
        self.options_gate = None
        self.options_disconnect = False
        self.options_started = threading.Event()
        self.posts = []
        self.hits = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                owner.hits.append((self.server.server_port, self.path))
                if self.path == "/options":
                    owner.options_started.set()
                    if owner.options_gate:
                        owner.options_gate.wait(timeout=5)
                    if owner.options_disconnect:
                        self.close_connection = True
                        self.connection.close()
                        return
                    time.sleep(0.15)
                    self.respond(b'{"routes":["domestic","international"]}', "application/json")
                else:
                    self.respond(owner.html().encode(), "text/html; charset=utf-8")

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                if length > 5 * 1024**2 or self.path != "/submit":
                    self.send_error(400)
                    return
                content = self.rfile.read(length)
                message = BytesParser(policy=policy.default).parsebytes(
                    ("Content-Type: " + self.headers["Content-Type"] + "\r\n\r\n").encode()
                    + content
                )
                owner.posts.append(
                    {
                        part.get_param("name", header="content-disposition"): part.get_payload(
                            decode=True
                        )
                        for part in message.iter_parts()
                    }
                )
                self.respond(b'{"received":true}', "application/json")

            def respond(self, content, content_type):
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Access-Control-Allow-Origin", owner.origin)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    self.wfile.write(content)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # Expected when the real connectivity test interrupts the client.

            def log_message(self, *args):
                pass

        self.web = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.api = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.origin = f"http://127.0.0.1:{self.web.server_port}"
        self.api_origin = f"http://127.0.0.1:{self.api.server_port}"
        self.threads = [
            threading.Thread(target=server.serve_forever, daemon=True)
            for server in [self.web, self.api]
        ]

    def html(self):
        button = (
            '<div role="button" onclick="next()">Continue</div>'
            if self.broken
            else '<button onclick="next()">Continue</button>'
        )
        return (
            (Path(__file__).parent / "compatibility/application.html")
            .read_text()
            .replace("__CONTINUE__", button)
            .replace("__API__", self.api_origin)
        )

    def __enter__(self):
        for thread in self.threads:
            thread.start()
        return self

    def __exit__(self, *args):
        for server in [self.web, self.api]:
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join()

    def journey(self):
        def target(role, name):
            return {"role": role, "name": name}

        def action(id, name, role="button"):
            return Step(id=id, action="activate", target=target(role, name), effect=True)

        return Journey(
            name="Hackyard multi-step compatibility",
            target=self.origin,
            allow_local=True,
            network={"navigation_origins": [self.api_origin]},
            privacy={"capture_page_text": True},
            steps=[
                Step(id="open", action="navigate"),
                action("validate", "Continue"),
                Step(id="errors", action="assert_errors"),
                Step(
                    id="name",
                    action="fill",
                    target=target("textbox", "Applicant name"),
                    value="Synthetic applicant",
                ),
                action("next", "Continue"),
                Step(
                    id="documents",
                    action="assert_visible",
                    target=target("heading", "Attach documents"),
                ),
                action("international", "International", "radio"),
                Step(
                    id="reference",
                    action="fill",
                    target=target("textbox", "Passport reference"),
                    value="TEST-ONLY",
                ),
                action("help", "Upload help"),
                Step(id="modal", action="assert_modal", target=target("dialog", "Upload help")),
                action("close", "Close help"),
                Step(id="restore", action="assert_focus", target=target("button", "Upload help")),
                Step(id="offline", action="offline"),
                Step(id="online", action="online"),
                Step(
                    id="retained",
                    action="assert_value",
                    target=target("textbox", "Passport reference"),
                    value="TEST-ONLY",
                ),
                Step(
                    id="upload",
                    action="upload",
                    file_label="Supporting document",
                    value_from="document",
                    effect=True,
                ),
                action("send", "Submit application"),
                Step(
                    id="done",
                    action="assert_visible",
                    target=target("heading", "Application received"),
                ),
                Step(id="audit", action="audit"),
            ],
        )

    def summary(self):
        return {
            "api_posts": len(self.posts),
            "api_options_requests": sum(path == "/options" for _, path in self.hits),
            "uploaded_bytes": [len(post["document"]) for post in self.posts],
        }
