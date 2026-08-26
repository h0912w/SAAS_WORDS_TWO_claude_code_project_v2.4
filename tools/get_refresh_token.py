"""
Google Ads OAuth2 Refresh Token 발급 스크립트.
실행 후 브라우저에서 승인하면 refresh_token을 출력한다.

사용법:
    python tools/get_refresh_token.py

필요 정보: Client ID, Client Secret (Google Cloud Console에서 발급)
"""

import json
import sys
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCOPE = "https://www.googleapis.com/auth/adwords"
REDIRECT_URI = "http://localhost:8080"
AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

_auth_code: str | None = None


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write("<h2>OK - 터미널로 돌아가세요</h2>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write("<h2>code 파라미터가 없습니다</h2>".encode("utf-8"))

    def log_message(self, *_):
        pass


def _load_env_local() -> dict:
    env_path = Path(__file__).parent.parent / ".env.local"
    values: dict = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    return values


def main():
    env = _load_env_local()
    client_id = env.get("GOOGLE_ADS_CLIENT_ID") or input("Client ID: ").strip()
    client_secret = env.get("GOOGLE_ADS_CLIENT_SECRET") or input("Client Secret: ").strip()
    print(f"Client ID: {client_id[:30]}...")

    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(auth_params)
    print(f"\n브라우저가 열립니다. Google 계정으로 승인 후 돌아오세요.\n{url}\n")
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8080), _Handler)
    server.handle_request()

    if not _auth_code:
        print("인증 코드를 받지 못했습니다.", file=sys.stderr)
        sys.exit(1)

    data = urllib.parse.urlencode({
        "code": _auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read())

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        print(f"refresh_token 없음. 응답: {token_data}", file=sys.stderr)
        sys.exit(1)

    print("\n=== .env.local 에 넣을 값 ===")
    print(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}")


if __name__ == "__main__":
    main()
