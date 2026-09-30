# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    & $Python -m venv build/venv
    if ($LASTEXITCODE -ne 0) { throw 'Build environment creation failed.' }
    $buildPython = Join-Path $projectRoot 'build/venv/Scripts/python.exe'
    & $buildPython -m pip install -r tools/requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & $buildPython -m PyInstaller --noconfirm --clean --onefile --windowed --specpath build --name Basketball-Score-Sheet-Stickers --icon "$projectRoot/assets/basketball.ico" --add-data "$projectRoot/assets/basketball.ico;assets" --add-data "$projectRoot/templates/score-sheet-stickers-2026.pdf;templates" app/generate_pdf.py
    if ($LASTEXITCODE -ne 0) { throw 'Windows application build failed.' }
    $packageRoot = Join-Path $projectRoot ('build/package-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $packageRoot | Out-Null
    Copy-Item -LiteralPath dist/Basketball-Score-Sheet-Stickers.exe,teams/sample/team-names_sample.csv,docs/Basketball-Score-Sheet-Stickers-Manual.pdf,LICENSE,THIRD-PARTY-NOTICES.md -Destination $packageRoot
    Copy-Item -LiteralPath licenses -Destination $packageRoot -Recurse
    $packageFiles = Get-ChildItem -LiteralPath $packageRoot | Select-Object -ExpandProperty FullName
    Compress-Archive -LiteralPath $packageFiles -DestinationPath dist/Basketball-Score-Sheet-Stickers-Windows-x64.zip -Force
    $packageHash = (Get-FileHash -LiteralPath dist/Basketball-Score-Sheet-Stickers-Windows-x64.zip -Algorithm SHA256).Hash.ToLower()
    "$packageHash  Basketball-Score-Sheet-Stickers-Windows-x64.zip" | Set-Content -LiteralPath dist/SHA256SUMS.txt -Encoding ascii
    Write-Output 'Built dist/Basketball-Score-Sheet-Stickers.exe and the Windows ZIP.'
} finally {
    Pop-Location
}
