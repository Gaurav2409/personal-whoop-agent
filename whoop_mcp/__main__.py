"""Local OAuth callback listener.

Run `python -m whoop_mcp.auth` — this opens the browser, listens on the
registered redirect port, exchanges the code, and stores tokens in keychain.
"""
import http.server
import sys
import threading
import urllib.parse as up

from . import auth, config


class _Handler(http.server.BaseHTTPRequestHandler):
    result = {"done": False}

    def do_GET(self):
        if "/callback" not in self.path:
            self.send_response(404)
            self.end_headers()
            return
        q = up.parse_qs(up.urlsplit(self.path).query)
        if "error" in q:
            _Handler.result = {"done": True, "error": q["error"][0]}
            self._respond("<h2>Authorization failed: %s</h2>" % q["error"][0])
            return
        _Handler.result = {"done": True, "code": q["code"][0], "state": q.get("state", [None])[0]}
        self._respond("<h2>WHOOP authorized. You can close this tab.</h2>")

    def _respond(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, *a):
        pass


def main():
    args = sys.argv[1:]
    if "--store" in args:
        # store client_id / secret / redirect interactively from keyring
        import getpass
        cid = input("Client ID: ").strip()
        secret = getpass.getpass("Client Secret: ")
        redirect = input(f"Redirect URI [{config.DEFAULT_REDIRECT}]: ").strip() or config.DEFAULT_REDIRECT
        config.set_credential("client_id", cid)
        config.set_credential("client_secret", secret)
        config.set_credential("redirect_uri", redirect)
        print("Stored in keychain (service whoop-dev-app).")
        return

    if "--status" in args:
        print(auth.token_status())
        return

    if "--revoke" in args:
        from . import client
        client.revoke()
        print("Tokens revoked/cleared.")
        return

    port = up.urlsplit(auth.get_redirect_uri()).port or 49152
    server = http.server.HTTPServer(("localhost", port), _Handler)
    url, state = auth.build_authorize_url()
    print("Opening browser for authorization…")
    print("If it doesn't open, paste this into a browser:")
    print(url)
    import webbrowser
    webbrowser.open(url)
    print(f"Listening on localhost:{port} …")
    server.timeout = 300
    server.handle_request()
    res = _Handler.result
    if not res.get("done"):
        print("Timed out waiting for callback.")
        return
    if "error" in res:
        print("Auth error:", res["error"])
        return
    # Complete PKCE exchange using the code directly (server got it via GET)
    code = res["code"]
    tokens = auth.exchange_code(code)  # exchange_code handles PKCE verifier? (see below)
    print("Authorized for WHOOP user:", tokens.get("user_id"), "| scope:", tokens.get("scope"))


if __name__ == "__main__":
    main()
