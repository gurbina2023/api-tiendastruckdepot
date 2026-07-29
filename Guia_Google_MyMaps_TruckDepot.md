# Mapa de cobertura Truck Depot en Google My Maps

Guía para dejar el mapa de promesas de entrega dentro de **Google My Maps** y que el operador de e‑commerce verifique cualquier dirección usando **el buscador de Google** (que en Guatemala encuentra más direcciones que OpenStreetMap).

Hay dos caminos:

- **Opción A — Importar el archivo KML** (rápido y exacto; recomendado).
- **Opción B — Dibujar los polígonos a mano** (si quieres crearlos o ajustarlos tú mismo).

En ambos casos, al final el operador usa la **barra de búsqueda del mapa** (Google) para comprobar direcciones.

---

## Opción A · Importar el KML (recomendado)

1. Abre **https://www.google.com/mymaps** e inicia sesión con la cuenta de Truck Depot.
2. Clic en **Crear un mapa nuevo**.
3. En el panel de la izquierda, sobre la primera capa, clic en **Importar**.
4. Sube el archivo **`TruckDepot_Cobertura.kml`**.
5. Aparecen los **polígonos de cobertura** (un color por tienda) y un **pin por sucursal**.
6. Ponle nombre al mapa (arriba a la izquierda), por ejemplo *"Cobertura de entrega — Truck Depot GT"*.

> **Sobre las capas:** My Maps permite hasta **10 capas** por mapa. Como hay 13 sucursales, es posible que agrupe algunas tiendas en la misma capa. No se pierde nada: **todos los polígonos se importan** y cada tienda mantiene su color. Si quieres control total por tienda, usa la Opción B (una capa por sucursal) o crea dos mapas por región.

---

## Cómo verifica el operador una dirección (¡el buscador de Google!)

Esta es la parte que resuelve el problema de las direcciones que OpenStreetMap no encontraba:

1. Abre el mapa de My Maps que acabas de crear.
2. En la **barra de búsqueda que está en la parte superior del mapa**, escribe la dirección del cliente (calle, avenida, zona, municipio…). **Esa barra usa el motor de Google Maps.**
3. Google coloca un **marcador** en el punto exacto, encima de tus polígonos de colores.
4. Mira **sobre qué polígono cae** el marcador y de **qué color** es → esa es la tienda que despacha, y el tiempo según la leyenda de colores.
5. Si el punto **no cae en ningún polígono**, no hay reparto local a domicilio desde una tienda cercana: aplica **envío nacional (24/48 h)**.

> Consejo: para conservar el punto, después de buscarlo puedes pulsar **"Añadir al mapa"** y quedará como marcador temporal; bórralo cuando termines para no ensuciar el mapa.

---

## Compartir el mapa con el equipo

1. Botón **Compartir** (icono de persona/enlace) en el panel izquierdo.
2. Elige **"Cualquier persona con el enlace puede ver"**.
3. Copia el enlace y compártelo con los operadores. Solo tú (dueño) puedes editarlo; ellos lo consultan.

---

## Opción B · Dibujar / ajustar los polígonos a mano

Úsala si prefieres crearlos desde cero o mover los límites.

1. **Crear un mapa nuevo** en My Maps y nómbralo.
2. Crea **una capa por sucursal** (botón **Añadir capa**; máximo 10 — combina tiendas cercanas si te quedas corto). Renómbralas con el nombre de la tienda.
3. Selecciona la capa de una tienda y usa la herramienta **"Dibujar una línea" → "Añadir línea o forma"**.
4. Haz clic para ir marcando el contorno del área de esa franja de tiempo y **cierra el polígono** haciendo clic en el punto inicial.
5. Ponle nombre al polígono, por ejemplo **"Guatemala — hasta 2 h"**.
6. Ábrelo y en **estilo** (icono del bote de pintura) elige **color de relleno, opacidad y color de borde**.
7. Repite por cada franja de tiempo y cada tienda. Agrega también un **marcador** en la ubicación de la tienda.

**¿Qué zonas van en cada polígono?** Abre el archivo **`Verificador_Cobertura_TruckDepot.html`**, pestaña **"Por sucursal"**, elige la tienda y verás la lista exacta de municipios/zonas por cada franja de tiempo. Esa es tu referencia para trazar.

---

## Leyenda de colores

**Por tienda** (así viene el KML — responde "¿qué tienda cubre aquí?"):

| Sucursal | Color |
|---|---|
| Guatemala | `#E6194B` rojo |
| Escuintla | `#3CB44B` verde |
| Chimaltenango 1 y 2 | `#4363D8` azul |
| Mazatenango | `#F58231` naranja |
| Villa Lobos | `#911EB4` morado |
| Puerto Barrios | `#00A8C6` celeste |
| Quetzaltenango | `#F032E6` magenta |
| Teculután | `#7A8B00` oliva |
| Atlántico | `#D2691E` terracota |
| Petén | `#2E8B57` verde mar |
| Huehuetenango | `#9A6324` café |
| Cobán | `#808000` verde oliva |
| Puerto Quetzal | `#000075` azul marino |

**Por tiempo** (opcional, si prefieres colorear por rapidez en la Opción B):

| Franja | Color |
|---|---|
| Mostrador / hasta 45 min | `#1A9850` verde |
| 1 h | `#66BD63` verde claro |
| 1.5 h | `#A6D96A` lima |
| 2 h | `#F5A70A` ámbar |
| 3 h | `#F46D43` naranja |
| 6 h | `#D73027` rojo |
| 24 / 48 h (nacional) | `#7A7A7A` gris |

---

## Ubicación de las tiendas (para colocar los pines)

Coordenadas de cada sucursal (lat, lng), tomadas del listado (CSV). Para colocar un pin en My Maps, pega la coordenada en la barra de búsqueda del mapa.

| Sucursal | Latitud, Longitud |
|---|---|
| Guatemala | 14.5764, -90.5457 |
| Escuintla | 14.3050, -90.7850 |
| Chimaltenango 1 y 2 | 14.6620, -90.8190 |
| Mazatenango | 14.5350, -91.5040 |
| Villa Lobos | 14.5450, -90.5720 |
| Puerto Barrios | 15.7278, -88.5944 |
| Quetzaltenango | 14.8683, -91.5501 |
| Teculután | 14.9876, -89.7246 |
| Atlántico | 14.6640, -90.4880 |
| Petén (San Benito / Santa Elena) | 16.9200, -89.8900 |
| Huehuetenango | 15.3197, -91.4711 |
| Cobán | 15.4708, -90.3711 |
| Puerto Quetzal / Puerto San José | 13.9250, -90.7850 |

---

## Notas y limitaciones

- Los polígonos son **áreas aproximadas** a nivel **municipio/zona**, no fronteras oficiales. El tiempo real depende de la dirección exacta.
- Las **aldeas, colonias y barrios** sin frontera pública se agrupan al área de su municipio, pero siguen apareciendo por su nombre en el verificador HTML.
- Las franjas de **24/48 h** son **envío nacional** (CEDI / "Departamentos"), por eso no se dibujan como zona.
- Para consultas rápidas por nombre de municipio/zona, el archivo **`Verificador_Cobertura_TruckDepot.html`** sigue siendo la vía más directa; My Maps es la mejor para **buscar direcciones reales** con el motor de Google.
