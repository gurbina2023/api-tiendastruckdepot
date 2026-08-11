# -*- coding: utf-8 -*-
"""Reconstruye la cobertura Truck Depot (Guatemala y Costa Rica) desde los CSV."""
import pandas as pd, json, unicodedata
from shapely.geometry import Point, mapping
from shapely.ops import unary_union

def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()

NAME_GT = {"GUATEMALA":"Guatemala","ESCUINTLA":"Escuintla","CHIMALTENANGO":"Chimaltenango",
        "MAZATENANGO":"Mazatenango","VILLA LOBOS":"Villa Lobos","PUERTO BARRIOS":"Puerto Barrios",
        "QUETZALTENANGO":"Quetzaltenango","TECULUTÁN":"Teculután","ATLÁNTICO":"Atlántico","PETÉN":"Petén",
        "HUEHUETENANGO":"Huehuetenango","COBÁN":"Cobán","PUERTO QUETZAL":"Puerto Quetzal",
        "FRAY BARTOLOMÉ":"Fray Bartolomé","QUICHÉ":"Quiché","RETALHULEU":"Retalhuleu","SAN MARCOS":"San Marcos"}
ORDER_GT = ["Guatemala","Escuintla","Chimaltenango","Mazatenango","Villa Lobos","Puerto Barrios",
         "Quetzaltenango","Teculután","Atlántico","Petén","Huehuetenango","Cobán","Puerto Quetzal",
         "Fray Bartolomé","Quiché","Retalhuleu","San Marcos"]
PALETTE_GT = ["#E6194B","#3CB44B","#4363D8","#F58231","#911EB4","#00A8C6",
           "#F032E6","#7A8B00","#D2691E","#2E8B57","#9A6324","#808000","#000075",
           "#FFB300","#00695C","#5D4037","#C2185B"]

NAME_CR = {"SAN JOSE":"San José","LIMON":"Limón","CARTAGO":"Cartago","CALDERA":"Caldera",
           "LIBERIA":"Liberia","MUELLE":"Muelle"}
ORDER_CR = ["San José","Cartago","Limón","Caldera","Liberia","Muelle"]
PALETTE_CR = ["#E6194B","#4363D8","#3CB44B","#F58231","#911EB4","#00A8C6"]

COUNTRIES = [
    {"code":"gt","country":"Guatemala","csv":"updates_csv/PROMES.CSV",
     "name":NAME_GT,"order":ORDER_GT,"palette":PALETTE_GT},
    {"code":"cr","country":"Costa Rica","csv":"updates_csv/PROMES_CR.CSV",
     "name":NAME_CR,"order":ORDER_CR,"palette":PALETTE_CR},
]

# radio de buffer (grados ~ 111 km) por tipo de destino -> "municipio/zona completos"
BUF = {"Municipio":0.075,"Cabecera":0.075,"Aldea":0.045,"Zona":0.032,"Colonia":0.030,"Barrio":0.030,
       "Punto carretera":0.030,"Puerto":0.030,"Instalación":0.030,"Sitio":0.030,"Tienda":0.030,
       "Calle":0.030,"Calzada":0.030,"Cantón":0.030,"Punto urbano":0.030,"Categoría interna":0.030}
def buf_for(t): return BUF.get(str(t), 0.04)

# entrega local (con polígono) hasta 12 horas; 24/48 h = envío nacional sin polígono
LOCAL_MAX = 720

geo_features, branch_meta, index_list = [], [], []
all_stores, all_order = {}, []   # para el KML

for C in COUNTRIES:
    df = pd.read_csv(C["csv"], encoding="utf-8-sig")
    df["Destino"] = df["Destino"].astype(str).str.strip()
    df["branch"] = df["Sucursal"].map(C["name"])
    assert df["branch"].notna().all(), C["code"] + " · Sucursal sin mapear: " + str(sorted(set(df[df.branch.isna()]['Sucursal'])))
    COLOR = {b: C["palette"][i] for i, b in enumerate(C["order"])}

    prom = df[df["Minutos"].notna()]
    MIN2LABEL = {int(m): str(l) for m, l in prom.groupby("Minutos")["Promesa de entrega"].first().items()}

    # ---- tiendas ----
    stores = {}
    for b, sub in df.groupby("branch"):
        ti = sub[sub["Tipo de destino"] == "Tienda"]
        if len(ti):
            stores[b] = [round(float(ti.iloc[0]["Latitud"]), 5), round(float(ti.iloc[0]["Longitud"]), 5)]
        else:
            mn = sub["Minutos"].min(); f = sub[(sub["Minutos"] == mn) & sub["Latitud"].notna()]
            stores[b] = [round(float(f["Latitud"].mean()), 5), round(float(f["Longitud"].mean()), 5)]
    all_stores.update(stores)
    all_order += [(C["code"], b, COLOR[b]) for b in C["order"]]

    # ---- geometría: unión de buffers, por banda acumulada (solo local <= LOCAL_MAX) ----
    for b in C["order"]:
        color = COLOR[b]; sub = df[df["branch"] == b]
        subp = sub[sub["Minutos"].notna()]
        st = stores[b]
        branch_meta.append({"name": b, "country": C["code"], "color": color, "store": st,
            "tiers": [{"label": MIN2LABEL[int(m)], "minutes": int(m)} for m in sorted(subp["Minutos"].unique())]})
        geo_features.append({"type":"Feature",
            "properties":{"kind":"store","country":C["code"],"branch":b,"color":color,"name":b},
            "geometry":{"type":"Point","coordinates":[st[1], st[0]]}})
        local = sorted(m for m in subp["Minutos"].unique() if m <= LOCAL_MAX)
        prev_area = -1
        for band in local:
            pts = subp[(subp["Minutos"] <= band) & subp["Latitud"].notna()]
            geoms = [Point(st[1], st[0]).buffer(0.030)]
            for _, r in pts.iterrows():
                geoms.append(Point(float(r["Longitud"]), float(r["Latitud"])).buffer(buf_for(r["Tipo de destino"])))
            poly = unary_union(geoms).simplify(0.004)
            if abs(poly.area - prev_area) < 1e-9:
                continue
            prev_area = poly.area
            geo_features.append({"type":"Feature",
                "properties":{"kind":"coverage","country":C["code"],"branch":b,"label":MIN2LABEL[int(band)],
                              "minutes":int(band),"color":color,"title":f"{b} — hasta {MIN2LABEL[int(band)]}"},
                "geometry": mapping(poly)})

    # ---- índice del buscador ----
    place_index = {}
    for _, r in prom.iterrows():
        dest = r["Destino"]; tipo = str(r["Tipo de destino"]); minu = int(r["Minutos"])
        muni = r["Municipio"] if pd.notna(r["Municipio"]) else None
        dep = r["Departamento"] if pd.notna(r["Departamento"]) else None
        if tipo == "Zona" and muni:
            key = f"{dest} ({muni})"
        elif muni and norm(dest) != norm(muni):
            key = f"{dest} ({muni})"
        else:
            key = dest
        coord = [round(float(r["Latitud"]),5), round(float(r["Longitud"]),5)] if pd.notna(r["Latitud"]) else None
        info = ", ".join(x for x in [muni, dep] if x) if muni or dep else "Envío nacional / interno"
        d = place_index.setdefault(key, {"entries":[], "coord":None, "info":info})
        d["entries"].append({"branch": r["branch"], "label": MIN2LABEL[minu], "minutes": minu, "local": minu <= LOCAL_MAX})
        if coord and d["coord"] is None: d["coord"] = coord
        if d["info"] == "Envío nacional / interno" and info != "Envío nacional / interno": d["info"] = info

    for place, d in place_index.items():
        seen, uniq = set(), []
        for e in sorted(d["entries"], key=lambda e: e["minutes"]):
            k = (e["branch"], e["label"])
            if k in seen: continue
            seen.add(k); uniq.append(e)
        index_list.append({"place": place, "country": C["code"], "coord": d["coord"], "info": d["info"], "entries": uniq})

index_list.sort(key=lambda x: norm(x["place"]))

geojson = {"type":"FeatureCollection","features":geo_features}
json.dump(geojson, open("coverage.geojson","w",encoding="utf-8"), ensure_ascii=False)

countries_meta = [{"code": C["code"], "name": C["country"]} for C in COUNTRIES]
json.dump({"countries":countries_meta, "branches":branch_meta, "index":index_list, "geo":geojson},
          open("payload.json","w",encoding="utf-8"), ensure_ascii=False)

# ---- KML ----
def kml_color(hexc, alpha):
    h = hexc.lstrip("#"); return (alpha + h[4:6] + h[2:4] + h[0:2]).lower()
def poly_kml(coords):
    ext = " ".join(f"{x:.5f},{y:.5f},0" for x, y in coords[0])
    holes = "".join("<innerBoundaryIs><LinearRing><coordinates>" +
                    " ".join(f"{x:.5f},{y:.5f},0" for x, y in h) +
                    "</coordinates></LinearRing></innerBoundaryIs>" for h in coords[1:])
    return ("<Polygon><outerBoundaryIs><LinearRing><coordinates>" + ext +
            "</coordinates></LinearRing></outerBoundaryIs>" + holes + "</Polygon>")
kml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
       '<name>Truck Depot - Cobertura de entrega (Guatemala y Costa Rica)</name>']
for i, (code, b, c) in enumerate(all_order):
    kml.append(f'<Style id="poly{i}"><LineStyle><color>{kml_color(c,"ff")}</color><width>2</width></LineStyle>'
               f'<PolyStyle><color>{kml_color(c,"44")}</color></PolyStyle></Style>')
    kml.append(f'<Style id="pin{i}"><IconStyle><color>{kml_color(c,"ff")}</color><scale>1.2</scale>'
               f'<Icon><href>http://maps.google.com/mapfiles/kml/shapes/truck.png</href></Icon></IconStyle></Style>')
for i, (code, b, c) in enumerate(all_order):
    kml.append(f"<Folder><name>{b} ({code.upper()})</name>")
    st = all_stores[b]
    kml.append(f'<Placemark><name>{b} (tienda)</name><styleUrl>#pin{i}</styleUrl>'
               f'<Point><coordinates>{st[1]:.5f},{st[0]:.5f},0</coordinates></Point></Placemark>')
    feats = [f for f in geo_features if f["properties"].get("kind")=="coverage"
             and f["properties"]["branch"]==b and f["properties"]["country"]==code]
    for f in sorted(feats, key=lambda x: -x["properties"]["minutes"]):
        g = f["geometry"]; title = f["properties"]["title"]
        if g["type"] == "Polygon":
            kml.append(f'<Placemark><name>{title}</name><styleUrl>#poly{i}</styleUrl>{poly_kml(g["coordinates"])}</Placemark>')
        else:
            kml.append(f'<Placemark><name>{title}</name><styleUrl>#poly{i}</styleUrl><MultiGeometry>' +
                       "".join(poly_kml(p) for p in g["coordinates"]) + "</MultiGeometry></Placemark>")
    kml.append("</Folder>")
kml.append("</Document></kml>")
open("TruckDepot_Cobertura.kml","w",encoding="utf-8").write("\n".join(kml))

# ---- informe ----
print("Sucursales:", len(branch_meta), "en", len(COUNTRIES), "países")
print("Polígonos:", sum(1 for f in geo_features if f['properties'].get('kind')=='coverage'))
print("Lugares únicos (buscador):", len(index_list))
print("Tiendas:")
for code, b, c in all_order: print(f"   {code} · {b:22s} {all_stores[b]}")
