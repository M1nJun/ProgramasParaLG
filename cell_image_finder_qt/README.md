
# Cell Image Finder (Qt)

Qt (PyQt6) UI to search JF2 image folders by **cell ID** under:

`<Drive>:\Files\Image\JF2\YYYY\MM\DD\HH\`

Searches:
- `NG`
- `OK\DL_CANDIDATE`
- `OK\DL_OK`

Inside the matching image folder (name contains `_<CELLID>`), it tries to find:
- `*_<CELLID>_EXT_DL_0_2.jpg`
- `*_<CELLID>_EXT_DL_1_2.jpg`

## Run

```bash
pip install -r requirements.txt
python main.py
```

## UI Notes

- Drive defaults to **E** but is editable.
- Sub path defaults to `Files\Image\JF2`.
- "Choose latest match only" picks newest by the `YYYYMMDD_HHMMSS` prefix in the folder name.
