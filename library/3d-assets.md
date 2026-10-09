# 3D assets — sources and intake

This note lists where a three.js scene can get models, HDRIs and textures without an account, and how to take a file in. Every source was checked on 2026-10-09 (S-AS-001–S-AS-010). Access and counts change, so check a source again when a request fails.

## Rules

- Take a source's own licence statement at its word. CC0, CC-BY and US-government public-domain works are allowed.
- Skip a source that needs an account, a key or a sign-up, or that answers with a bot challenge.
- Send a stock Chrome User-Agent and nothing that identifies the user or the project.
- Download model, texture, environment and licence files only. Never run, install or open in a browser anything that came with them.
- Run `scripts/assets/check_asset.py` on every model, image and archive before a scene loads it.
- Record each file in the run's `assets-manifest.md` with its pinned source URL, licence, author, credit text and SHA-256.

## Sources

| Source | Use for | Licence | How to fetch |
|---|---|---|---|
| Poly Haven (S-AS-001/002) | Realistic models, HDRIs, PBR textures | CC0, site-wide | `GET https://api.polyhaven.com/assets?t=models` (or `hdris`, `textures`, or `/search?q=…`), then `GET https://api.polyhaven.com/files/{id}`. Each file entry gives its URL, size and md5. |
| Smithsonian 3D (S-AS-003) | Real-scale museum scans | CC0, Smithsonian Open Access | `GET https://3d-api.si.edu/api/v1.0/content/file/search?q={term}&file_type=glb&quality=Low&rows=10`. Each `uri` is a direct GLB. `quality` is `Thumb`, `Low` or `High`. |
| NASA 3D Resources (S-AS-004) | Spacecraft | "Free and without copyright", per its README | `https://raw.githubusercontent.com/nasa/NASA-3D-Resources/{commit}/3D%20Models/{Name}/{file}.glb`. List the files with the GitHub git-trees API. |
| Khronos glTF-Sample-Assets (S-AS-005) | Clean GLBs and material tests | Per model, in `Models/{Name}/metadata.json` | Index at `Models/model-index.json`. File at `https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/{commit}/Models/{Name}/glTF-Binary/{Name}.glb`. |
| ambientCG (S-AS-006) | PBR textures, HDRIs | CC0, site-wide | `GET https://ambientcg.com/api/v2/full_json?type=Material&q={term}&include=downloadData` (or `type=HDRI`), then the zip from `https://ambientcg.com/get?file={name}.zip`. |
| Kenney (S-AS-007) | Stylised low-poly only | CC0, with `License.txt` in each zip | Read the zip link from `https://kenney.nl/assets/{slug}`. The link carries a hash that changes. |

Notes by source:

- **Poly Haven** models are glTF with a separate `.bin` and JPG textures, not GLB. Fetch every file listed under the model's `include`. Each asset lists `dimensions` in millimetres and a `polycount`.
- **Smithsonian** GLBs are Draco-compressed and in metres. The pages on `3d.si.edu` sit behind a bot challenge, but the API does not.
- **NASA** has 257 GLBs, some as large as 96 MB. Skip the `.7z` archives. Credit NASA.
- **Khronos** holds mostly test and showcase props. Use a model only when every entry in its `legal` list has `spdx` set to `CC0-1.0` or `CC-BY-4.0`. That rule drops Damaged Helmet (CC-BY-NC), Duck (SCEA), Sponza, Brain Stem and the two Dragons. Credit each CC-BY author.
- **ambientCG** has only a few 3D models, and they are OBJ. One person runs the site, so keep the request count low.
- **Kenney** models have toy proportions, so they don't suit a real-scale scene.

## Other sources checked

- **Sketchfab and BlenderKit.** Downloads need an account (HTTP 401 and 403).
- **Poly Pizza.** The site shows a bot challenge, and the API needs a key.
- **Thingiverse and Printables.** Both show a bot challenge, and both are mostly STL.
- **Wikimedia Commons.** It accepts STL only as a 3D format.
- **OpenGameArt.** Licences vary by asset, and the CC0 pack that was tested held only a `.unitypackage`.
- **Google Poly.** It has shut down.
- **Objaverse on Hugging Face** (S-AS-008). The GLBs download, and the metadata gives each object's licence and author. Most objects are CC-BY, but many are NC or SA. Use only CC0 and CC-BY objects, and expect uneven quality and scale.
- **three.js `examples/models`** (S-AS-009). Its MIT licence covers the code. Several models are non-commercial or carry no licence at all, so don't take models from it.
- **Searching GitHub for models** (S-AS-010). Code search doesn't index binary GLBs. The sampled `.glb` hits were Git LFS pointers or not glTF. Search can't filter by asset licence, and a repo's licence usually covers only its code. Use GitHub to host a pinned repo you already know, not to find assets.

## Intake

1. **Pin the source.** For a GitHub file, put the commit SHA in the URL. For Poly Haven, keep the md5 from the API and compare it after the download.
2. **Fetch with limits.**

   ```bash
   curl --proto '=https' -fsSL --max-filesize 200000000 --max-time 300 \
     -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36' \
     -o FILE URL
   ```

   Prefer single-file downloads to clones. If you must clone, set `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_LFS_SKIP_SMUDGE=1` first, because a global git config can rewrite URLs and add credentials.
3. **Check every model, image and archive.** Run `python3 scripts/assets/check_asset.py FILE...` from the workshop root. A `.gltf` covers the `.bin` and textures it references, so pass the `.gltf`, not its parts. The check fails on remote or escaping file references, Git LFS pointers, broken GLB structure, oversized buffers or images, and unsafe archive entries. It prints each file's SHA-256 and the loaders the file needs. `--help` lists every check.
4. **Archives.** The check lists a zip without extracting it. Extract only the entries you need, by name, and then check the extracted model. A model can reference textures outside its own file, and the check reports any that are missing. For example, Kenney GLBs load a shared `Textures/colormap.png`:

   ```bash
   unzip ARCHIVE 'Models/GLB format/firetruck.glb' 'Models/GLB format/Textures/*' -d DEST
   ```
5. **Record.** Add one row per file to the run's `assets-manifest.md`.
6. **Load.** Take decoders from the pinned three.js package, never from the download or a CDN. Draco files need `DRACOLoader` with `setDecoderPath` pointing at `three/examples/jsm/libs/draco/`. Meshopt files need `meshopt_decoder.module.js` from `three/examples/jsm/libs/`. KTX2 textures need `KTX2Loader` with `three/examples/jsm/libs/basis/`.
