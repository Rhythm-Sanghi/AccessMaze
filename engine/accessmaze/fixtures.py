from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from time import sleep

STYLE = """<style>body{font:18px system-ui;max-width:700px;margin:60px auto;color:#202a33}
label,button,[role=button]{display:block;margin:18px 0}input{font:inherit;padding:8px}
button,[role=button]{padding:12px;border:1px solid #444;background:#edf2f5;cursor:pointer}
:focus-visible{outline:3px solid #245cbe;outline-offset:4px}</style>"""


def fixture_html(kind):
    modal = (
        """<button id="help">Application help</button>
<div role="dialog" aria-modal="true" aria-label="Application help" id="modal" hidden>
<p>Help text</p><button id="close">Close help</button></div>"""
        if kind == "modal"
        else ""
    )
    conditional = (
        """<label><input type="checkbox" id="international">International applicant</label>
<section id="extra"></section>"""
        if kind == "conditional"
        else ""
    )
    picker = '<button id="date">Choose date</button>'
    if kind == "broken":
        picker = '<div role="button" id="date">Choose date</div>'
    error = '<p id="error">Please enter a name.</p>'
    if kind != "errors":
        error = '<p id="error" role="alert">Please enter a name.</p>'
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Scholarship application — {kind}</title>{STYLE}<main>
<h1>Scholarship application</h1><p>Local synthetic test fixture: {kind}</p>
<label for="name">Applicant name</label><input id="name" autocomplete="off">
{picker}<p id="selection" role="status"></p>
<button id="submit">Review application</button><section id="result"></section>
<button id="restart">Start again</button><p id="connection" role="status">Online</p>
{modal}{conditional}
{'<button id="unnamed"></button>' if kind == "broken" else ""}
</main><script>
const nameInput=document.querySelector('#name');
document.querySelector('#date').onclick=()=>{{
 document.querySelector('#selection').textContent='Date selected';
}};
document.querySelector('#submit').onclick=()=>{{
 if(!nameInput.value){{
  document.querySelector('#result').innerHTML={error!r};
  nameInput.setAttribute('aria-invalid','true');
  {'nameInput.setAttribute("aria-describedby","error");' if kind != "errors" else ""}
 }}else{{document.querySelector('#result').innerHTML='<h2>Application ready</h2>'}}
}};
document.querySelector('#restart').onclick=()=>{{
 document.querySelector('#result').textContent='';
 document.querySelector('#selection').textContent='';nameInput.value='';
}};
if(document.querySelector('#help')){{
 document.querySelector('#help').onclick=()=>document.querySelector('#modal').hidden=false;
 document.querySelector('#close').onclick=()=>document.querySelector('#modal').hidden=true;
}}
if(document.querySelector('#international')){{
 document.querySelector('#international').onchange=e=>{{
  document.querySelector('#extra').innerHTML=e.target.checked?
   '<label for="passport">Passport reference</label><input id="passport" required>':'';
 }};
 document.querySelector('#submit').onclick=()=>{{
  const passport=document.querySelector('#passport');
  if(!nameInput.value || (passport && !passport.value)){{
   document.querySelector('#result').innerHTML='<p role="alert">Complete the required fields.</p>';
  }}else{{
   document.querySelector('#result').innerHTML='<h2>Application ready</h2>'+
    '<button id="final">Submit synthetic application</button>';
   document.querySelector('#final').onclick=()=>{{
    document.querySelector('#result').innerHTML='<h2>Application submitted</h2>';
   }};
  }}
 }};
}}
window.addEventListener('offline',()=>document.querySelector('#connection').textContent='Offline');
window.addEventListener('online',()=>{{
 document.querySelector('#connection').textContent='Online';
 {'nameInput.value="";' if kind == "recovery" else ""}
}});
</script></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        kind = self.path.strip("/")
        if kind not in {
            "accessible",
            "broken",
            "errors",
            "recovery",
            "branch",
            "slow",
            "modal",
            "conditional",
        }:
            self.send_error(404)
            return
        content = fixture_html(kind).encode("utf-8")
        if kind == "slow":
            sleep(1)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args):
        pass


class FixtureServer:
    def __init__(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def url(self, target):
        return f"http://127.0.0.1:{self.server.server_port}/{target.split('://')[1]}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
