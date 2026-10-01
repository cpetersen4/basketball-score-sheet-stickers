# Developer guide

The [README](README.md) covers downloading, using, and printing from the Windows app. This guide covers the source code, file format, artwork, and developer tools.

## Repository files

| Location | Purpose |
| --- | --- |
| `app/` | PDF generator and Windows interface. |
| `templates/score-sheet-stickers-2026.ai` | Editable Adobe Illustrator artwork. |
| `templates/score-sheet-stickers-2026.pdf` | Two-page PDF template with six home and six away stickers. |
| `assets/` | Basketball icon and related images. |
| `teams/sample/` | Fictional sample roster. |
| `tests/` | PDF generation and interface tests. |
| `tools/` | Build, manual generation, artwork obfuscation, and package verification tools. |
| `docs/` | PDF manual, documentation images, and security check records. |

Real team folders are ignored by Git. Only the team-folder instructions and fictional sample are tracked. See [teams/README.md](teams/README.md). Do not add real names to tracked examples or public issues.

## CSV format

Save the roster as a UTF-8 `.csv` or `.txt` file with exactly these three columns:

```csv
number,name,role
7,Example Player,Player
na,Example Head Coach,Head Coach
na,Example Assistant,Assistant Coach
```

Supported roles are `Player`, `Head Coach`, and `Assistant Coach`. Use 1–15 players, unique jersey numbers containing 1–3 digits, and at most one head coach. Coaching rows are optional. Quote names containing commas. Player order follows the file; unused player slots are cleared.

The [sample CSV](teams/sample/team-names_sample.csv) contains fictional names. Keep a real roster and its generated PDFs in an ignored team folder. When importing a CSV, the app's Save dialog starts in that folder.

## Run from source

Use Python 3.12 on 64-bit Windows for the tested development setup:

```powershell
python -m pip install -r tools/requirements.txt
python app/generate_pdf.py
```

With no arguments, the script opens the interface. To generate a PDF from the command line:

```powershell
python app/generate_pdf.py teams/sample/team-names_sample.csv output/sample-stickers.pdf --team "Sample Team"
```

Use `--template` for a different PDF exported with the same placeholder structure. The original template and existing output files are never overwritten.

The generator uses pypdf, pdfminer.six, and ReportLab. It removes template text, preserves graphics and page dimensions, and inserts the roster using Windows Arial. Names shrink to fit their cells; text that would become too small to read is rejected. Both imported and manually entered rosters receive validation.

## Build the Windows package

```powershell
powershell -ExecutionPolicy Bypass -File tools/build-windows.ps1
```

The build uses an isolated environment in `build/venv/` and creates a standalone EXE and ZIP in `dist/`. The ZIP includes the app, fictional sample CSV, illustrated PDF manual, license, and third-party notices. Build outputs are ignored by Git.

The EXE bundles Python, the PDF libraries, template, and basketball icon. Windows Arial and a PDF viewer are supplied by the user's computer. The app works offline and makes no network requests. It targets Windows 10/11 x64 and has been tested on Windows 11.

## Tests and release checks

```powershell
python -m unittest discover -s tests -v
python tools/verify_windows_package.py
```

Run the package verification after building. It extracts the ZIP and generates a PDF with the EXE while removing external Python settings from the environment.

GitHub's Windows workflow runs tests, code scanning, dependency auditing, package building, and standalone verification. Additional security check records are in [docs/SECURITY-CHECKS.md](docs/SECURITY-CHECKS.md).

## Update the artwork

Open the Illustrator file, keep the layout aligned with the reference score sheet, and export a PDF with the expected team, player, and coach placeholders. Each sticker must contain all 15 player fields. Check the export at actual size. The PDF generator works independently of Illustrator.

To replace original names with placeholders, run `tools/obfuscate-names.jsx` in Illustrator through **File > Scripts > Other Script**. It reads a roster CSV to identify the original names, replaces them with placeholders such as `Player 01` and `Head Coach 01`, saves in `templates/`, and creates a backup in the Windows temporary folder.

## Regenerate the manual

```powershell
python tools/create_manual.py
```

This uses ReportLab and the images in `docs/`. Render and visually inspect updated manual pages before publishing.

## License and third-party material

The [personal-use license](LICENSE) requires written permission for redistribution, publication of copies, resale, and commercial exploitation. Private installation copies, backups, and modifications are permitted under its terms.

Third-party libraries retain their own licenses; see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). The original score sheet reference embedded in the Illustrator artwork retains its original ownership. This app is independently developed and does not claim affiliation with the score sheet publisher.
