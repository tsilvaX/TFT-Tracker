Drop tactician GLB files here.

The UI checks these candidate filenames for the favorite tactician:

- the Data Dragon tactician id, for example `60001.glb`
- the normalized tactician name, for example `chibi_malphite.glb`
- the normalized base name without "Chibi", for example `malphite.glb`

If no matching GLB exists, the app renders the procedural 3D fallback model.

Sprite fallbacks live in `static/assets/`. Chibi Malphite currently uses
`static/assets/chibi_malphite_fallback.png`; other tacticians fall back to
`static/assets/default_tactician_spirit.png`.
