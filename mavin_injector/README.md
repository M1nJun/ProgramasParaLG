# MAVIN Model Injector (Python / PySide6)

Inject (copy) a folder's contents into a MAVIN model folder under:

- `C:\VisionPC\Bin\MAVIN` (known to sometimes appear as `mavin`)

## Behavior

- **Overwrite-only**: copies source files into the target model folder and overwrites existing files.
  Files/folders that are already in the target but not present in the source are **left untouched**.
- **Backup**: copies the entire **source folder** into:
  - `<ModelFolder>\DL_VERSION\<SourceFolderName>`
  If that backup folder already exists, it uses `<SourceFolderName>_1`, `_2`, etc.

## Run (dev)

```bash
pip install -r requirements.txt
python app.py
```

## Build EXE (PyInstaller)

Install:
```bash
pip install pyinstaller
```

Recommended (folder distribution, most reliable for PySide6):
```bash
pyinstaller --noconsole --name "MavinModelInjector" --onedir app.py
```

Optional (single exe, can be slower to start):
```bash
pyinstaller --noconsole --name "MavinModelInjector" --onefile app.py
```

Output will be in `dist/`.
