# Publicar el verificador en una URL para los agentes

> **⚠️ ACTUALIZACIÓN (julio 2026):** el proyecto ahora se publica en **Railway** y el token de Mapbox **ya no va dentro del HTML**: vive únicamente en el servidor, como variable de entorno `MAPBOX_TOKEN` (pestaña *Variables* del servicio en Railway). La búsqueda de direcciones la hace el servidor a través del endpoint `/geocode`, así que los agentes no ven ni ingresan ningún token, y el token **no debe llevar restricción de URL** en Mapbox (las peticiones salen del servidor, no de una página web). Los pasos de abajo describen el método anterior (archivo estático con token incrustado) y se conservan solo como referencia.

Objetivo: dejar el archivo **`index.html`** en una dirección web (URL) para que los agentes de servicio al cliente solo la abran y busquen direcciones, **sin configurar nada**. El administrador lo hace **una sola vez**.

El motor de búsqueda de direcciones es **Mapbox**. El **token de Mapbox ya viene puesto** dentro de `index.html`, así que en principio solo falta **publicarlo** y **restringir el token a tu URL** para que nadie más pueda usarlo.

Resumen: **(1)** (opcional) confirmar/cambiar el token → **(2)** publicar el archivo en una URL → **(3)** restringir el token a esa URL → **(4)** repartir el enlace.

---

## Paso 1 · El token de Mapbox (ya incluido)

El archivo ya trae el token. Si algún día necesitas cambiarlo:

1. Abre **`index.html`** con un editor de texto (Bloc de notas, VS Code…).
2. Cerca del inicio verás:
   ```js
   const CONFIG = { mapboxToken: "pk.xxxxx..." };
   ```
3. Reemplaza el valor entre comillas por el nuevo token (empieza con `pk.`) y guarda.

> Si lo dejas vacío (`""`), la app igual funciona: cada agente podría pegar su token en el navegador, o usar el modo sin token (Abrir en Google Maps + pegar coordenadas).

**¿Necesitas un token nuevo?** Crea una cuenta gratis en **mapbox.com**, entra a **account.mapbox.com → Access tokens**, y usa el *Default public token* (o crea uno nuevo; empieza con `pk.`). El plan gratuito de Mapbox incluye un uso mensual generoso para geocodificación.

---

## Paso 2 · Publicar el archivo (elige UNA opción)

### Opción A — Google Cloud Storage
1. En **Cloud Storage**, crea un **bucket** (nombre único, p. ej. `td-cobertura`).
2. Sube **`index.html`** al bucket.
3. Habilítalo como web: da **lectura pública** al objeto (o configura el bucket como *sitio web estático*).
4. Tu URL quedará como: `https://storage.googleapis.com/td-cobertura/index.html`

### Opción B — Servidor / intranet interno *(mejor para acceso solo interno)*
1. Copia **`index.html`** a la carpeta pública de tu servidor web (IIS, Apache, Nginx) o intranet.
2. Quedará en una URL interna, p. ej.: `https://intranet.truckdepot.com/cobertura/index.html`
3. Ideal si quieres que **solo se acceda desde la red corporativa / VPN**.

### Opción C — Rápida (Netlify Drop)
1. Entra a **app.netlify.com/drop** y **arrastra la carpeta** que contiene `index.html`.
2. Te da una URL `https://algo.netlify.app` al instante. (Puedes renombrar el sitio.)

> **SharePoint / Google Sites:** no alojan bien apps HTML con scripts (las encierran en un iframe restringido y el mapa puede no cargar). Úsalos para **enlazar o incrustar por URL** la app ya publicada con A, B o C — no como alojamiento principal.

---

## Paso 3 · Restringir el token a tu URL *(importante para la seguridad)*

Así, aunque el token sea visible en el código, **solo funciona desde tu dirección**.

1. Entra a **account.mapbox.com → Access tokens** y abre el token que estás usando (o créalo).
2. En **URL restrictions** (Restricciones de URL), agrega la(s) URL desde donde se abrirá la página:

   | Dónde publicaste | URL a permitir |
   |---|---|
   | Google Cloud Storage | `https://storage.googleapis.com/td-cobertura/*` |
   | Servidor / intranet | `https://intranet.truckdepot.com/*` |
   | Netlify | `https://tu-sitio.netlify.app/*` |

3. Guarda. A partir de ahí, el token rechaza cualquier uso desde otro sitio.

> Nota: las restricciones por URL usan el dominio de la página. Si abres `index.html` como **archivo local** (`file://`) con el token restringido, fallará; por eso se publica en una URL. Para pruebas locales, usa un token sin restricción.

---

## Paso 4 · Repartir y probar

1. Comparte la URL con los agentes (que la guarden como favorito).
2. Abre la URL y prueba: escribe una dirección y pulsa **Buscar**. Arriba debe decir **"Búsqueda con Mapbox activada (configurada por el administrador)"** y marcar el punto con la tienda y el tiempo de entrega.

---

## Control de acceso (quién puede entrar)

- **Cloud Storage público / Netlify:** cualquiera con el enlace puede ver la página. Los datos de cobertura **no son sensibles**; el único riesgo es el uso del token, y eso queda cubierto con la **restricción por URL** del Paso 3.
- **Solo interno:** usa la **Opción B** (servidor tras VPN/SSO) o Google Cloud con **IAP (Identity-Aware Proxy)** para exigir inicio de sesión corporativo.

---

## Actualizar el mapa a futuro

Cuando cambien las promesas de entrega, se regenera `index.html` y se **reemplaza** el archivo publicado. **El token y la URL no cambian**, así que los agentes no tienen que hacer nada.

---

## Solución de problemas

- **"Mapbox rechazó la consulta (401)":** el token no es válido, está deshabilitado, o la **URL** desde donde se abre no está en la lista de URLs permitidas del token.
- **Funciona en un lugar y en otro no:** revisa que la URL exacta (con `https://` y `/*` al final) esté en las *URL restrictions* del token.
- **Abierto como archivo local (`file://`) y no busca:** un token restringido por URL no funciona en archivos locales; publícalo en una URL o usa un token sin restricción para pruebas. (La búsqueda por nombre de municipio/zona sí funciona sin conexión ni token.)
- **No encuentra una dirección:** agrega más detalle (zona, municipio, departamento) o usa el botón **Abrir en Google Maps ↗** y pega las coordenadas.
