# 🏀 Basketball Score Sheet Stickers

A Windows app for preparing basketball score sheet stickers with your team's player names, jersey numbers, and coaches. Enter up to 15 players and print six home and six away stickers.

**[⬇️ Download the Windows app](https://github.com/cpetersen4/basketball-score-sheet-stickers/releases/latest/download/Basketball-Score-Sheet-Stickers-Windows-x64.zip)** · [📖 PDF manual](docs/Basketball-Score-Sheet-Stickers-Manual.pdf) · [🐛 Report a bug](https://github.com/cpetersen4/basketball-score-sheet-stickers/issues)

---

## 💻 What you need

| Requirement | Details |
| --- | --- |
| Computer | **Windows only:** Windows 10 or 11, 64-bit. Tested on Windows 11. |
| To open and print the stickers | A PDF viewer. |
| To print on labels | A printer and full-sheet 8.5 × 11-inch label paper. |

No internet connection, Python, or Adobe Illustrator is needed to run the app. Support for other operating systems could be added on request; [submit a request here](https://github.com/cpetersen4/basketball-score-sheet-stickers/issues).

## ⬇️ Download and open

1. [Download the Windows app](https://github.com/cpetersen4/basketball-score-sheet-stickers/releases/latest/download/Basketball-Score-Sheet-Stickers-Windows-x64.zip).
2. Right-click the downloaded ZIP file and select **Extract All**.
3. Open the extracted folder and double-click **Basketball-Score-Sheet-Stickers.exe**.

There is nothing to install. The download includes the app, a sample team list, and a PDF manual.

## 📝 Enter your team

### 1. Load roster

Choose **Skip CSV / Enter manually** to type in your team. If you already have a team list saved as a CSV or TXT file, choose **Choose CSV / TXT** to import it.

![Load roster screen](docs/screenshots/load-roster.png)

### 2. Review team

Enter the team name, player names, and jersey numbers. Coaches are optional; enter assistant coaches one per line. Leave unused player rows blank. Scroll down if all 15 rows are not visible.

![Review team screen](docs/screenshots/review-team.png)

### 3. Save PDF

Choose where to save the PDF, then click **Create printable PDF**. Use **Open saved PDF** to open it for printing.

> **Before closing:** Save your PDF first. Your entries are cleared when you close the app, but saved PDFs remain available.

Click the steps at the top or use **Back** to review your entries. Choose a new filename for each PDF; existing files will not be overwritten.

![Example generated score sheet stickers](docs/sample-output.png)

## 🖨️ Print and cut

1. Use **full-sheet 8.5 × 11-inch adhesive label paper**, such as [this label paper](https://a.co/d/0fz6G47o) or Staples full-sheet shipping label paper. Choose paper suitable for your printer, with one label covering the whole sheet.
2. Open the saved PDF and choose the home or away page you need.
3. Select **Letter (8.5 × 11 inches)** paper and **Actual size / 100%** in the print dialog. The pages are landscape.
4. Check a plain-paper test print against the score sheet before printing on label paper.
5. Cut out the stickers with a **straight paper cutter or scissors**. Peel off the backing and attach each sticker to the team roster area on the score sheet.

> **Print setting:** Use **Actual size / 100%**. Do **not** use Fit, Shrink, or Scale to fit.

## 📋 Optional: import a team list

The download includes **team-names_sample.csv** as an example. Use a copy for your own team, or enter the names directly in the app. The [CSV format instructions](DEVELOPMENT.md#csv-format) explain the required columns if you want to prepare a file.

## ❓ Help and bug reports

The [PDF manual](docs/Basketball-Score-Sheet-Stickers-Manual.pdf) includes printing instructions and help with common problems. [Report a bug](https://github.com/cpetersen4/basketball-score-sheet-stickers/issues) with what you were doing and any error message shown. Please leave player names and other personal information out of public reports.

Source code, artwork editing, and build instructions are in the [developer guide](DEVELOPMENT.md).

---

## 📄 Permission to use

Free for personal, noncommercial use, including preparing score sheets for your team. You may print and share your team's generated score sheets. Redistributing or reselling the app requires the owner's written permission. See the [license](LICENSE) for the full terms.
