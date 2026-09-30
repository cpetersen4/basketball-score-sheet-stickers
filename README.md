# EYBA Score Sheet Stickers

Printable team roster stickers for Edmonton Youth Basketball Association (EYBA) score sheets, prepared for the 2026 season. The stickers let scorekeepers add the team name, player names, jersey numbers, and coaching staff to a score sheet without handwriting the roster for every game.

The current artwork uses **Sample Team** and obvious placeholders for player and coach names, with separate home and away roster layouts.

## Files

| File | Purpose |
| --- | --- |
| [eyba-score-sheet-stickers-2026.ai](eyba-score-sheet-stickers-2026.ai) | Editable Adobe Illustrator artwork. |
| [eyba-score-sheet-stickers-2026.pdf](eyba-score-sheet-stickers-2026.pdf) | Printable PDF containing repeated home and away roster stickers. |
| [source/EYBA Regular Scoresheet 2026.pdf](source/EYBA%20Regular%20Scoresheet%202026.pdf) | Original one-page EYBA score sheet used as the layout reference. |

## Printing and use

1. Open the sticker PDF in a PDF viewer.
2. Select the home or away sticker page as needed.
3. Print at **100% / actual size**, with automatic page scaling disabled so the roster layout keeps its intended dimensions.
4. Check a plain-paper test print against the score sheet before printing on adhesive paper.
5. Cut out the roster stickers and attach them to the appropriate team roster area on the score sheet.

## Updating the artwork

Open the `.ai` file in Adobe Illustrator to change the team name, roster, jersey numbers, or coaches. Keep the layout aligned with the reference score sheet, update each repeated sticker, and export a new PDF for printing. Check the export at actual size before use.

This repository stores design files and PDF exports; there is no application to install or build.

## Obfuscating names

Run `scripts/obfuscate-names.jsx` in Illustrator through **File > Scripts > Other Script**. The script reads a roster CSV with `number,name,role` columns to identify the original names and replaces them with `Player 01`, `Head Coach 01`, and `Asst Coach 01` placeholders. It saves the root Illustrator file and places a backup in the Windows temporary folder.

Real team files in any `private-team/` folder are excluded from Git by `.gitignore`.
