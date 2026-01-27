# MAVIN Model Injector (SMB Multi-PC)

Inject (overwrite-only copy) model contents into MAVIN model folders on multiple Vision PCs over SMB:

- `\\<ip>\C$\VisionPC\Bin\MAVIN\<ModelFolder>`

## Behavior

- **Overwrite-only**: overwrites same-name files, leaves other existing target files/folders untouched.
- **Backup**: copies the entire **source folder** into:
  - `<ModelFolder>\DL_VERSION\<SourceFolderName>`
  If that backup folder already exists, it uses `<SourceFolderName>_1`, `_2`, etc.
- **Models dropdown uses INTERSECTION** of selected PCs (case-insensitive by folder name).

## Dry Run (marker)

Writes a marker file into:

- `<ModelFolder>\DL_VERSION\_INJECT_DRY_RUN_<timestamp>.txt`

Includes:
- source folder
- target model folder
- planned backup folder path
- list of relative files that would be copied

## Configure PCs

Edit `pcs.json` at the project root.

## Run (dev)

```bash
pip install -r requirements.txt
python app.py
```

## Build EXE (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --noconsole --name "MavinModelInjector" --onedir app.py
```
