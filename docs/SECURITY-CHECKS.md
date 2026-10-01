# Release security and verification

Checks run on Windows 11 on 2026-09-30 for version 1.0.0:

- Nine unit/integration tests: passed (15-player PDF replacement, validation, manual entry, navigation state, and overwrite protection).
- Bandit 1.9.4 scanned all app source: no medium/high findings. One low-severity B606 finding was reviewed: `os.startfile` opens only the generated PDF path stored after successful generation. No shell command string is constructed.
- pip-audit 2.10.1: no known vulnerabilities in the pinned direct dependencies or the resolved isolated build environment.
- Gitleaks 8.30.1: repository history and the release commit scanned with redacted reports; no secrets detected.
- Microsoft Defender custom scan of the release directory: completed without an error; no detections associated with this directory.
- Extracted ZIP smoke test: EXE generated both pages and all 15 player slots with Python environment variables removed and PATH limited to Windows System32.
- EXE resources: basketball icon present. ZIP contents: EXE, fictional CSV, PDF manual, personal-use license, and third-party notices; no text quick-start.
- Four-page manual rendered and visually checked. README app screenshots and generated-sheet preview use fictional names. Private team folders are excluded by Git.

These checks describe this build and do not guarantee absence of all vulnerabilities. Windows 10 is a compatibility target; the package was tested on Windows 11.

The GitHub Windows workflow repeats tests, medium/high Bandit checks, dependency auditing, and portable build verification for PRs and pushes to main. It does not replace the local Defender or Gitleaks checks.

The AGPL PDF engine was replaced with permissive pypdf, pdfminer.six, and ReportLab to support the requested permission-based distribution terms. pypdf was updated to 6.19.0 before the final audit; all build dependencies are pinned. Generated pages were rendered and visually checked after the engine replacement.

## Follow-up bug sweep (2026-09-30)

The follow-up fixes duplicate CSV headers, invisible text sizing, malformed/repeated template rows, template text retained in nested PDF forms, incomplete output files after failed writes, and access to all rows on smaller screens. Seventeen regression/integration tests pass, including exclusive-file-creation race protection and scroll/keyboard navigation. The Windows package was rebuilt and verified independently of external Python. Dependency auditing remains clear; Bandit has no medium/high findings.
