# -*- coding: utf-8 -*-
# Servidor para Railway (solo librería estándar).
# - Sirve index.html y los demás archivos estáticos.
# - Endpoint /geocode?q=<dirección>: consulta la API de Geocoding de Google
#   Maps usando la clave de la variable de entorno GOOGLE_MAPS_API_KEY. Así la
#   clave vive solo en el servidor y nunca llega al navegador de los usuarios.
import json
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import urlopen

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()


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
        if not GOOGLE_MAPS_API_KEY:
            return self.send_json(503, {"message": "El servidor no tiene configurada la variable GOOGLE_MAPS_API_KEY."})
        if not q or len(q) > 300:
            return self.send_json(400, {"message": "Falta la dirección a buscar."})
        url = (
            "https://maps.googleapis.com/maps/api/geocode/json?address=" + quote(q)
            + "&key=" + quote(GOOGLE_MAPS_API_KEY)
            + "&components=country:GT&language=es&region=gt"
        )
        try:
            with urlopen(url, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8"))
        except (HTTPError, URLError):
            return self.send_json(502, {"message": "No se pudo consultar el servicio de mapas."})
        status = data.get("status", "")
        if status == "ZERO_RESULTS" or (status == "OK" and not data.get("results")):
            return self.send_json(200, {"found": False})
        if status != "OK":
            msg = data.get("error_message", "")
            return self.send_json(502, {"message": "Google Maps respondió " + status + (": " + msg if msg else "")})
        r0 = data["results"][0]
        loc = r0["geometry"]["location"]
        return self.send_json(200, {
            "found": True,
            "lat": loc["lat"],
            "lng": loc["lng"],
            "label": r0.get("formatted_address", "Ubicación"),
        })

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
    if not GOOGLE_MAPS_API_KEY:
        print("AVISO: GOOGLE_MAPS_API_KEY no está definido; /geocode responderá 503.")
    print(f"Sirviendo en http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
