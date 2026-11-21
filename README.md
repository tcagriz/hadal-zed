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

## Update and uninstall

To update, replace the copied `hadal.json` with the latest file and reload Zed.
To uninstall, remove that file and choose another theme.

## Support and source

Report Zed-specific issues in the
[issue tracker](https://github.com/tcagriz/hadal-zed/issues). Source changes are made
in the [Hadal Theme Suite](https://github.com/tcagriz/hadal-theme) monorepo and
mirrored here.

## License

MIT. Includes a third-party notice for Microsoft's VS Code Abyss theme in
[LICENSE](LICENSE).
