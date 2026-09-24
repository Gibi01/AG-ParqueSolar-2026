const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

test("solicita un solo mosaico visible, identificado y con caché normal", async () => {
    const calls = [];
    const revoked = [];
    const sandbox = {
        document: {
            createElement: () => ({
                setAttribute() {},
                set src(value) {
                    this.source = value;
                    queueMicrotask(() => this.onload());
                }
            })
        },
        fetch: async (url, options) => {
            calls.push({url, options});
            return {ok: true, blob: async () => ({tile: true})};
        },
        URL: {
            createObjectURL: () => "blob:mock-tile",
            revokeObjectURL: (url) => revoked.push(url)
        }
    };
    const source = fs.readFileSync(
        path.join(__dirname, "..", "src", "visualization", "osm_tiles.js"),
        "utf8"
    );
    vm.runInNewContext(source, sandbox);

    class TileLayer {
        constructor(url, options) {
            this.url = url;
            this.options = options;
        }
        getTileUrl(coords) {
            return this.url.replace("{z}", coords.z)
                .replace("{x}", coords.x).replace("{y}", coords.y);
        }
        static extend(methods) {
            return class extends TileLayer {
                createTile(coords, done) {
                    return methods.createTile.call(this, coords, done);
                }
            };
        }
    }

    const layer = sandbox.createIdentifiedOsmTileLayer(
        {TileLayer}, "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        {attribution: "© OpenStreetMap contributors"}, "AG-ParqueSolar-2026"
    );
    const tile = await new Promise((resolve, reject) => {
        layer.createTile({z: 9, x: 164, y: 308}, (error, element) => {
            if (error) reject(error);
            else resolve(element);
        });
    });

    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "https://tile.openstreetmap.org/9/164/308.png");
    assert.equal(calls[0].options.headers["X-Requested-With"], "AG-ParqueSolar-2026");
    assert.equal(calls[0].options.cache, "default");
    assert.equal(calls[0].options.mode, "cors");
    assert.equal(tile.source, "blob:mock-tile");
    assert.deepEqual(revoked, ["blob:mock-tile"]);
});
