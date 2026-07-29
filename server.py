# -*- coding: utf-8 -*-
# Servidor estático mínimo para Railway (solo librería estándar).
# Sirve index.html y los demás archivos del proyecto en el puerto
# que Railway asigna por la variable de entorno PORT.
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Sirviendo en http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
