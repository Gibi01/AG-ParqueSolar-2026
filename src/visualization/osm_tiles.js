// OSM permite X-Requested-With para mapas abiertos desde file://, donde el
// navegador no puede enviar un Referer web válido. Solo se pide el mosaico
// visible que Leaflet solicita; fetch usa la caché HTTP normal del navegador.
function createIdentifiedOsmTileLayer(leaflet, tilesUrl, options, appId) {
    const IdentifiedTileLayer = leaflet.TileLayer.extend({
        createTile: function (coords, done) {
            const tile = document.createElement("img");
            tile.alt = "";
            tile.setAttribute("role", "presentation");

            fetch(this.getTileUrl(coords), {
                method: "GET",
                mode: "cors",
                cache: "default",
                headers: {"X-Requested-With": appId}
            }).then(function (response) {
                if (!response.ok) {
                    throw new Error("OSM tile HTTP " + response.status);
                }
                return response.blob();
            }).then(function (blob) {
                const objectUrl = URL.createObjectURL(blob);
                tile.onload = function () {
                    URL.revokeObjectURL(objectUrl);
                    done(null, tile);
                };
                tile.onerror = function () {
                    URL.revokeObjectURL(objectUrl);
                    done(new Error("No se pudo mostrar el mosaico OSM"), tile);
                };
                tile.src = objectUrl;
            }).catch(function (error) {
                done(error, tile);
            });
            return tile;
        }
    });
    return new IdentifiedTileLayer(tilesUrl, options);
}
