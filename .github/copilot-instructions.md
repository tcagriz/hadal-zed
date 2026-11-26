# Hadal for Zed instructions

## Mirror policy

- This repository is a synchronized mirror of the `zed/` directory in
  [tcagriz/hadal-theme](https://github.com/tcagriz/hadal-theme).
- Make primary source changes in `hadal-theme/zed/`, sync them with
  `scripts/sync.sh zed`, and submit mirror changes through a pull request.
- Never push directly to `main`.
- Bug reports and feature requests belong in the `hadal-theme` monorepo.
  Suspected vulnerabilities must use its private vulnerability report.
- `themes/hadal.json` is generated from `palette/palette.json` by the
  monorepo generator. Do not hand-edit it.
- `extension.toml`, `README.md` and `LICENSE` are hand-written package files.

## Development rules

- Keep the extension manifest, theme metadata, README and repository metadata
  consistent.
- The extension ID must remain unique in the Zed registry. Do not choose or
  change an ID without checking the current registry for collisions.
- Keep the current `$schema` identifier and valid Zed theme schema shape.
- Preserve terminal ANSI colors, UI states and syntax coverage when changing
  mappings.
- Do not add one-off colors outside the shared Hadal palette.
- Do not claim catalog availability until the package is actually accepted.

## Validation

Run the checks available in the source monorepo. At minimum:

```sh
python3 tests/check_extension.py --package /tmp/hadal-zed-extension.tar.gz
python3 -m unittest tests/check_extension_test.py
python3 -m json.tool themes/hadal.json > /dev/null
python3 -c 'import pathlib, tomllib; tomllib.loads(pathlib.Path("extension.toml").read_text())'
```

When Zed is available, use **Extensions → Install Dev Extension** with this
repository, then verify that the Hadal theme appears in the Theme Selector and
loads without errors. Confirm that `LICENSE` remains at the package root.
