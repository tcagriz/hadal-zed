# Hadal for Zed

A deep-sea dark theme for [Zed](https://zed.dev), based on the VS Code Abyss theme.

## Install

Hadal is **not currently published in the Zed extension catalog**. The catalog
contains a different extension named Hadal, so do not install it by searching for
`Hadal` in the Extensions panel.

Install this theme manually by copying `themes/hadal.json` to:

| Platform | Theme directory |
| --- | --- |
| macOS and Linux | `~/.config/zed/themes/` |
| Windows | `%USERPROFILE%\AppData\Roaming\Zed\themes\` |

For macOS or Linux:

```sh
mkdir -p ~/.config/zed/themes
cp themes/hadal.json ~/.config/zed/themes/hadal.json
```

Then select **Hadal** in Zed's Theme Selector, or add it to `settings.json`:

```json
"theme": {
  "mode": "dark",
  "light": "One Light",
  "dark": "Hadal"
}
```

Use any light theme you prefer for the `light` value.

## Validate a development extension

From the `zed/` package root:

```sh
python3 tests/check_extension.py --package /tmp/hadal-zed-extension.tar.gz
```

In Zed, open **Extensions → Install Dev Extension**, select this repository,
then open the Theme Selector and choose **Hadal**. Reload the window if needed
and confirm the editor, terminal and UI render without errors.

## Update and uninstall

To update, replace the copied `hadal.json` with the latest file and reload Zed.
To uninstall, remove that file and choose another theme.

## Support and source

Ask installation and usage questions in
[Hadal Discussions](https://github.com/tcagriz/hadal-theme/discussions). Report
reproducible Zed-specific bugs through the
[Hadal issue chooser](https://github.com/tcagriz/hadal-theme/issues/new/choose).
Source changes are made in the
[Hadal Theme Suite](https://github.com/tcagriz/hadal-theme) monorepo and mirrored
here. Suspected vulnerabilities must use the monorepo's
[private security report form](https://github.com/tcagriz/hadal-theme/security/advisories/new).

## License

MIT. Includes a third-party notice for Microsoft's VS Code Abyss theme in
[LICENSE](LICENSE).
