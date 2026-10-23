// Turns the d3-celestial star catalogue (stars.6.json, GeoJSON) into the flat file the home page draws as its background.
//   bun scripts/build-stars.mjs <path to stars.6.json> [path to constellations.lines.json]
// Output: public/stars.json = { "n": count, "stars": [ra°, dec°, magnitude, B-V, ...] }, brightest stars to magnitude 5.5.
// The catalogue is BSD-licensed (see public/licences.txt). Coordinates are J2000; RA is stored wrapped to ±180°.
import { readFileSync, writeFileSync } from 'node:fs';

const src = process.argv[2];
if (!src) throw new Error("usage: bun scripts/build-stars.mjs <stars.6.json> [constellations.lines.json]");
const MAX_MAG = 5.5;
const features = JSON.parse(readFileSync(src, 'utf8')).features.filter((f) => f.properties.mag <= MAX_MAG);
const r = (x, d) => Math.round(x * 10 ** d) / 10 ** d;
const stars = features
  .sort((a, b) => a.properties.mag - b.properties.mag)
  .flatMap((f) => {
    const [lon, dec] = f.geometry.coordinates;
    const ra = lon < 0 ? lon + 360 : lon;
    return [r(ra, 2), r(dec, 2), r(f.properties.mag, 1), r(parseFloat(f.properties.bv) || 0.6, 2)];
  });
writeFileSync(new URL('../public/stars.json', import.meta.url), JSON.stringify({ n: stars.length / 4, stars }));
console.log(`${stars.length / 4} stars written`);

// Optional second argument: constellations.lines.json from the same project. Writes public/constellation-lines.json with
// the few constellations drawn faintly behind the graph, as flat polylines [ra°, dec°, ra°, dec°, ...].
const linesSrc = process.argv[3];
if (linesSrc) {
  const DRAWN = ['UMa', 'Leo']; // Ursa Major, Leo
  const lines = JSON.parse(readFileSync(linesSrc, 'utf8'))
    .features.filter((f) => DRAWN.includes(f.id))
    .flatMap((f) => f.geometry.coordinates.map((line) => line.flatMap(([lon, dec]) => [r(lon < 0 ? lon + 360 : lon, 2), r(dec, 2)])));
  writeFileSync(new URL('../public/constellation-lines.json', import.meta.url), JSON.stringify({ lines }));
  console.log(`${lines.length} constellation polylines written`);
}
