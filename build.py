# -*- coding: utf-8 -*-
import re, json
from unidecode import unidecode
from geonamescache import GeonamesCache
from shapely.geometry import MultiPoint, mapping
from shapely.ops import unary_union
from data import BRANCHES, MANUAL_COORDS, CAPITAL_ZONAS

BUF = 0.022  # ~2.4 km de margen alrededor del casco convexo
GT_BBOX = (-92.4, 13.5, -88.1, 17.9)  # lng_min, lat_min, lng_max, lat_max

def norm(s):
    s = unidecode(s).lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s.rstrip(". ")

# ---- diccionario de coordenadas: geonamescache (GT) + manual ----
gc = GeonamesCache()
COORDS = {}
for c in gc.get_cities().values():
    if c["countrycode"] == "GT":
        COORDS.setdefault(norm(c["name"]), [round(c["latitude"], 5), round(c["longitude"], 5)])
COORDS.update({norm(k): v for k, v in MANUAL_COORDS.items()})

HUEHUE = [15.3210, -91.4700]
COBAN = [15.4703, -90.3745]
MIXCO = COORDS.get("mixco", [14.6308, -90.6071])
VILLANUEVA = COORDS.get("villa nueva", [14.5251, -90.5854])
AMATITLAN = COORDS.get("amatitlan", [14.4774, -90.6349])

VN_HINTS = ("vn", "villa nueva", "barcena", "peronia", "castanas",
            "catalina linda vista", "monte maria", "plan grande", "el frutal",
            "mayan golf", "villa lobos", "ulises rojas", "delta barcena", "linda vista")

MAXDIST = 1.05  # grados (~115 km): una cobertura local no puede estar más lejos de su tienda

# overrides por sucursal para nombres genéricos que colisionan entre regiones
BRANCH_OVERRIDES = {
    "Escuintla": {"la democracia": [14.2170, -90.9330]},
    "Mazatenango": {"santa barbara": [14.5000, -91.3670]},
    "Petén": {"la libertad": [16.7830, -90.1170], "san antonio": [16.9500, -89.8800],
              "san miguel": [16.9000, -89.9500], "san pedro": [16.9500, -89.9500],
              "san juan dios": [16.8700, -89.9000]},
    "Huehuetenango": {"la libertad": [15.6300, -91.9200], "la democracia": [15.6300, -91.9200],
                       "santa barbara": [15.4000, -91.7830]},
}

def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

def resolve(place, branch, store=None):
    n = norm(place)
    ov = BRANCH_OVERRIDES.get(branch, {})
    if n in ov:
        return ov[n]
    cand = _resolve_raw(n, branch)
    if cand is None:
        return None
    if store is not None and _dist(cand, store) > MAXDIST:
        return None  # resolución demasiado lejos -> se agrupa a la tienda
    return cand

def _resolve_raw(n, branch):
    # zonas dependientes de la sucursal
    m = re.search(r"zona (\d+)", n)
    if m and (n.startswith("zona") or "mixco" not in n):
        z = int(m.group(1))
        if branch == "Huehuetenango":
            return HUEHUE
        if branch == "Cobán":
            return COBAN
        if branch in ("Guatemala", "Atlántico"):
            return CAPITAL_ZONAS.get(z)
    # Mixco / Villa Nueva / Amatitlán (colonias)
    if "mixco" in n:
        return MIXCO
    if "amatitlan" in n:
        return AMATITLAN
    if any(h in (" " + n + " ") if len(h) == 2 else h in n for h in VN_HINTS):
        return VILLANUEVA
    # exacto
    if n in COORDS:
        return COORDS[n]
    # limpieza de prefijos y reintento
    cleaned = re.sub(r"\b(centro|carr|km|al|aldea|barrio|colonia|pto|sn|de|del|la|el|los|las|hasta|carre)\b", " ", n)
    cleaned = re.sub(r"[^a-z ]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned in COORDS:
        return COORDS[cleaned]
    # última pista: algún municipio conocido contenido como palabra
    for key in ("palin", "escuintla", "monterrico", "iztapa"):
        if key in cleaned.split():
            return COORDS.get(key)
    return None

# 13 colores distintos por sucursal
PALETTE = ["#E6194B", "#3CB44B", "#4363D8", "#F58231", "#911EB4", "#00A8C6",
           "#F032E6", "#7A8B00", "#D2691E", "#2E8B57", "#9A6324", "#808000", "#000075"]

def hex_to_kml(hexc, alpha="ff"):
    hexc = hexc.lstrip("#")
    r, g, b = hexc[0:2], hexc[2:4], hexc[4:6]
    return (alpha + b + g + r).lower()

def canon_place(p, branch):
    """Etiqueta única para el buscador: desambigua 'Zona N' entre ciudades."""
    m = re.match(r"^Zona\s*0*(\d+)\s*$", p.strip())
    if m:
        num = int(m.group(1))
        if branch in ("Guatemala", "Atlántico"):
            return f"Zona {num} (Ciudad de Guatemala)"
        if branch == "Cobán":
            return f"Zona {num} (Cobán)"
    return p

# ---- construir geometría, KML y datos ----
geo_features = []
place_index = {}      # place display -> list of {branch,label,minutes,local}
resolved_count = 0
unresolved = []
branch_meta = []

for i, br in enumerate(BRANCHES):
    color = PALETTE[i % len(PALETTE)]
    name = br["name"]
    store = br["store"]
    branch_meta.append({"name": name, "color": color, "store": store,
                        "tiers": [{"label": t[0], "minutes": t[1]} for t in br["tiers"]]})
    # punto de tienda
    geo_features.append({"type": "Feature",
        "properties": {"kind": "store", "branch": name, "color": color, "name": name},
        "geometry": {"type": "Point", "coordinates": [store[1], store[0]]}})

    cum_pts = [(store[1], store[0])]  # (lng,lat)
    prev_sig = None
    for label, minutes, places in br["tiers"]:
        local = minutes <= 360
        # index (todas las franjas, para el buscador)
        for p in places:
            rc = resolve(p, name, store)
            if rc is None:
                unresolved.append((name, p))
                coord = None
            else:
                resolved_count += 1
                coord = [rc[0], rc[1]]
            disp = canon_place(p, name)
            place_index.setdefault(disp, {"entries": [], "coord": None})
            place_index[disp]["entries"].append({"branch": name, "label": label,
                                                  "minutes": minutes, "local": local})
            if coord and place_index[disp]["coord"] is None:
                place_index[disp]["coord"] = coord
        if not local:
            continue
        # acumular puntos resueltos de esta franja para el polígono
        for p in places:
            rc = resolve(p, name, store)
            if rc is not None:
                lng, lat = rc[1], rc[0]
                if GT_BBOX[0] <= lng <= GT_BBOX[2] and GT_BBOX[1] <= lat <= GT_BBOX[3]:
                    cum_pts.append((lng, lat))
        sig = tuple(sorted(set((round(x, 4), round(y, 4)) for x, y in cum_pts)))
        if sig == prev_sig:
            continue
        prev_sig = sig
        poly = MultiPoint(cum_pts).convex_hull.buffer(BUF)
        geo_features.append({"type": "Feature",
            "properties": {"kind": "coverage", "branch": name, "label": label,
                           "minutes": minutes, "color": color,
                           "title": f"{name} — hasta {label}"},
            "geometry": mapping(poly)})

geojson = {"type": "FeatureCollection", "features": geo_features}

# ---- escribir GeoJSON ----
with open("coverage.geojson", "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False)

# ---- escribir KML ----
def poly_kml(coords):
    # coords: lista de anillos; primero es exterior
    ext = coords[0]
    ring = " ".join(f"{x:.5f},{y:.5f},0" for x, y in ext)
    inner = ""
    for hole in coords[1:]:
        h = " ".join(f"{x:.5f},{y:.5f},0" for x, y in hole)
        inner += f"<innerBoundaryIs><LinearRing><coordinates>{h}</coordinates></LinearRing></innerBoundaryIs>"
    return (f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{ring}</coordinates>"
            f"</LinearRing></outerBoundaryIs>{inner}</Polygon>")

kml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
       '<name>Truck Depot - Cobertura de entrega (Guatemala)</name>']
# estilos
for i, br in enumerate(BRANCHES):
    c = PALETTE[i % len(PALETTE)]
    kml.append(f'<Style id="poly{i}"><LineStyle><color>{hex_to_kml(c,"ff")}</color><width>2</width></LineStyle>'
               f'<PolyStyle><color>{hex_to_kml(c,"44")}</color></PolyStyle></Style>')
    kml.append(f'<Style id="pin{i}"><IconStyle><color>{hex_to_kml(c,"ff")}</color><scale>1.2</scale>'
               f'<Icon><href>http://maps.google.com/mapfiles/kml/shapes/truck.png</href></Icon></IconStyle></Style>')

for i, br in enumerate(BRANCHES):
    name = br["name"]
    kml.append(f"<Folder><name>{name}</name>")
    st = br["store"]
    kml.append(f'<Placemark><name>{name} (tienda)</name><styleUrl>#pin{i}</styleUrl>'
               f'<Point><coordinates>{st[1]:.5f},{st[0]:.5f},0</coordinates></Point></Placemark>')
    # polígonos de esta sucursal (de mayor a menor tiempo para que el rápido quede arriba)
    feats = [f for f in geo_features if f["properties"].get("kind") == "coverage"
             and f["properties"]["branch"] == name]
    for f in sorted(feats, key=lambda x: -x["properties"]["minutes"]):
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "Polygon" else None
        title = f["properties"]["title"]
        if g["type"] == "Polygon":
            kml.append(f'<Placemark><name>{title}</name><styleUrl>#poly{i}</styleUrl>{poly_kml(g["coordinates"])}</Placemark>')
        elif g["type"] == "MultiPolygon":
            kml.append(f'<Placemark><name>{title}</name><styleUrl>#poly{i}</styleUrl><MultiGeometry>')
            for part in g["coordinates"]:
                kml.append(poly_kml(part))
            kml.append("</MultiGeometry></Placemark>")
    kml.append("</Folder>")
kml.append("</Document></kml>")
with open("TruckDepot_Cobertura.kml", "w", encoding="utf-8") as f:
    f.write("\n".join(kml))

# ---- exportar datos para el HTML ----
index_list = []
for place, d in place_index.items():
    seen, uniq = set(), []
    for e in sorted(d["entries"], key=lambda e: e["minutes"]):
        k = (e["branch"], e["label"])
        if k in seen:
            continue
        seen.add(k); uniq.append(e)
    index_list.append({"place": place, "coord": d["coord"], "entries": uniq})
index_list.sort(key=lambda x: unidecode(x["place"]).lower())

payload = {"branches": branch_meta, "index": index_list, "geo": geojson}
with open("payload.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)

# ---- informe ----
total_places = sum(len(t[2]) for br in BRANCHES for t in br["tiers"])
print(f"Sucursales: {len(BRANCHES)}")
print(f"Lugares (todas las franjas): {total_places}")
print(f"Coordenadas resueltas (para geometría): {resolved_count}")
print(f"Sin resolver (se agrupan a la tienda): {len(unresolved)}")
print(f"Polígonos generados: {sum(1 for f in geo_features if f['properties'].get('kind')=='coverage')}")
print(f"Lugares únicos en el buscador: {len(index_list)}")
# validar bbox de todos los puntos usados
bad = []
for f in geo_features:
    if f["properties"].get("kind") == "store":
        x, y = f["geometry"]["coordinates"]
        if not (GT_BBOX[0] <= x <= GT_BBOX[2] and GT_BBOX[1] <= y <= GT_BBOX[3]):
            bad.append((f["properties"]["branch"], x, y))
print("Tiendas fuera de bbox GT:", bad if bad else "ninguna")
print("\nEjemplos sin resolver:", unresolved[:15])
