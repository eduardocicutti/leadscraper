# Sidecar binary

Compile `main.py` with PyInstaller as `scraper-sidecar`, then place the
target-suffixed executable in this folder before running `tauri build`.

On Windows with the MSVC Rust target, Tauri expects:

```text
src-tauri/binaries/scraper-sidecar-x86_64-pc-windows-msvc.exe
```

The `tauri.conf.json` entry remains `binaries/scraper-sidecar`; Tauri appends
the target triple during bundling.
