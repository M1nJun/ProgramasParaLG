
# Cell Image Finder (Qt) — v2 (Date Range + Date List)

## What’s new
- **Option A: Date Range** (Start/End)
- **Option B: Date List** (paste a non-contiguous set of dates)
- Updated to a more modern white UI (Fusion + stylesheet)

## Run
```bash
pip install -r requirements.txt
python main.py
```

## How matching works
For each cell ID, the program searches under:
`<Drive>:\Files\Image\JF2\YYYY\MM\DD\HH\`
and scans:
- `NG`
- `OK\DL_CANDIDATE`
- `OK\DL_OK`

It then looks for:
- `*_<CELLID>_EXT_DL_0_2.jpg`
- `*_<CELLID>_EXT_DL_1_2.jpg`

### “Choose latest match only”
If the same cell ID appears multiple times across the searched dates/hours,
it picks the folder with the **latest** `YYYYMMDD_HHMMSS` prefix.
