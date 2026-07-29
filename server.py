# -*- coding: utf-8 -*-
# Servidor para Railway (solo librería estándar).
# - Sirve index.html y los demás archivos estáticos.
# - Endpoint /geocode?q=<dirección>: consulta la API de Mapbox usando el
#   token de la variable de entorno MAPBOX_TOKEN. Así el token vive solo
#   en el servidor y nunca llega al navegador de los usuarios.
import json
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import urlopen

MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "").strip()


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        if urlparse(self.path).path == "/geocode":
            self.geocode()
        else:
            super().do_GET()

    def geocode(self):
        q = parse_qs(urlparse(self.path).query).get("q", [""])[0].strip()
        if not MAPBOX_TOKEN:
            return self.send_json(503, {"message": "El servidor no tiene configurada la variable MAPBOX_TOKEN."})
        if not q or len(q) > 300:
            return self.send_json(400, {"message": "Falta la dirección a buscar."})
        url = (
            "https://api.mapbox.com/search/geocode/v6/forward?q=" + quote(q)
            + "&access_token=" + quote(MAPBOX_TOKEN)
            + "&country=gt&limit=1&language=es"
        )
        try:
            with urlopen(url, timeout=10) as r:
                self.send_json_raw(200, r.read())
        except HTTPError as e:
            self.send_json_raw(e.code, e.read())
        except URLError:
            self.send_json(502, {"message": "No se pudo consultar el servicio de mapas."})

    def send_json(self, code, obj):
        self.send_json_raw(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def send_json_raw(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    if not MAPBOX_TOKEN:
        print("AVISO: MAPBOX_TOKEN no está definido; /geocode responderá 503.")
    print(f"Sirviendo en http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
