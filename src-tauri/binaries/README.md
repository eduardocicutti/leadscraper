# Sidecar binary

Build the Python backend + Playwright Chromium with:

```powershell
.\build-sidecar.bat
```

This produces:

```text
src-tauri/binaries/scraper-sidecar-x86_64-pc-windows-msvc.exe
src-tauri/binaries/ms-playwright/          # bundled Chromium for Tauri
```

Tauri bundles `ms-playwright/` as a resource and passes `PLAYWRIGHT_BROWSERS_PATH` to the sidecar at runtime.

## Standalone test (without Tauri)

```powershell
.\build-sidecar.bat
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\dist\ms-playwright"
.\dist\scraper-sidecar.exe
```

Then open `http://127.0.0.1:8000/health`.

## Full desktop build

```powershell
.\build-sidecar.bat
npm run tauri build
```

Installer output: `src-tauri/target/release/bundle/`
