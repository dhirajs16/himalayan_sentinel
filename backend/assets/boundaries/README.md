# Nepal administrative map context

Publisher: **Open Knowledge Nepal, LocalBoundaries**. Data license: **CC BY 4.0**,
as stated in the [publisher's license notice](https://localboundries.oknp.org/about/)
and [dataset repository README](https://github.com/openknowledgenp/localboundaries/blob/54f496a289670ab4fd781d8191c12a0f4cad7c15/README.md).
The repository's separate MIT license concerns software; it is not the data license.

Attribution: Administrative boundaries: Open Knowledge Nepal, LocalBoundaries,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
<https://localboundries.oknp.org/>.

These two GeoJSON files preserve upstream bytes at revision
`54f496a289670ab4fd781d8191c12a0f4cad7c15` (2026-07-04); only filenames changed.
`manifest.json` records download paths, SHA-256 hashes and feature counts.
The bundled license notice accompanies the data. There are 77 districts and seven
provinces, WGS84/EPSG:4326. Every polygon was checked for validity and unique
district names. Upstream derives districts by dissolving local-level boundaries.
The survey date is unspecified. These are contextual polygons, not certified
emergency jurisdictions or flood footprints; no publisher endorsement is implied.

Runtime maps, district filtering, population summaries and administrative imports
use these files. The original `data/GeoJson/` files have unknown provenance, remain
untouched and ignored, and are no longer served or used by those features.
Population caches include boundary hashes and are recomputed for this source.
Synthetic tests can explicitly inject a separate boundary directory.
