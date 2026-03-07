"""
DL Crop image cache / index.

Responsibilities:
    - Pre-scan crop folders once and build an in-memory index.
    - Provide O(1) lookup of crop images by cell_id.
    - Cache drive locations so we never re-scan drives.

Usage:
    cache = CropCache()
    cache.build_index(model_id, date_str, log_fn)
    files = cache.lookup(cell_id="a635K06000", side="LOWER",
                         crop_folder="Crop_A", match_tokens=["A_L"])
"""

import os
from typing import List, Dict, Callable, Optional
from collections import defaultdict

from config import CROP_DEFECT_MAP, get_available_drives
from core.crop_locator import find_mavin_across_drives


class CropCache:
    """
    Pre-indexes crop image folders for fast cell_id lookup.

    After build_index() is called, all crop folders needed for the
    current set of defects have been scanned and their filenames
    indexed by cell_id. Subsequent lookups are pure in-memory dict access.
    """

    def __init__(self):
        # Maps crop_folder -> full resolved path on disk
        # e.g. {"Crop_A": "F:\\Files\\Image\\JF2\\2026\\03\\06\\Mavin\\Crop_A"}
        self._folder_paths: Dict[str, Optional[str]] = {}

        # Maps (crop_folder, cell_id) -> list of (filepath, filename) tuples
        # This is the main lookup index
        self._file_index: Dict[tuple, List[tuple]] = defaultdict(list)

        # Track which crop folders we've already indexed
        self._indexed_folders: set = set()

    def build_index(
        self,
        model_id: str,
        date_str: str,
        defect_types: set = None,
        on_progress: Callable[[str], None] = None,
    ):
        """
        Pre-scan and index all crop folders needed for the given defect types.

        Args:
            model_id: Model name (e.g. "JF2").
            date_str: Date in YYYYMMDD format.
            defect_types: Set of JUDGE-DEFECT values to prepare for.
                          If None, indexes ALL configured crop folders.
            on_progress: Optional log callback.
        """
        def log(msg: str):
            if on_progress:
                on_progress(msg)

        # Determine which crop folders we need
        folders_needed = self._get_needed_folders(defect_types)
        if not folders_needed:
            return

        log(f"Pre-indexing {len(folders_needed)} crop folder(s)...")

        drives = get_available_drives()

        for crop_folder in folders_needed:
            if crop_folder in self._indexed_folders:
                continue

            # Find the folder on disk (cached after first find)
            crop_path = self._resolve_folder(crop_folder, model_id, date_str, drives)
            if crop_path is None:
                log(f"  {crop_folder}: not found on any drive")
                self._indexed_folders.add(crop_folder)
                continue

            # Index all files in this folder
            file_count = self._index_folder(crop_folder, crop_path)
            log(f"  {crop_folder}: indexed {file_count} files")
            self._indexed_folders.add(crop_folder)

    def lookup(
        self,
        cell_id: str,
        side: str,
        crop_folder: str,
        match_tokens: List[str],
    ) -> List[str]:
        """
        Fast lookup of crop images for a cell.

        Args:
            cell_id: Cell ID to match.
            side: "UPPER" or "LOWER".
            crop_folder: Which crop folder to search in.
            match_tokens: Additional tokens that must appear in filename.

        Returns:
            List of full file paths matching all criteria.
        """
        candidates = self._file_index.get((crop_folder, cell_id), [])
        if not candidates:
            return []

        matched = []
        for filepath, filename in candidates:
            if side not in filename:
                continue
            if all(token in filename for token in match_tokens):
                matched.append(filepath)

        return sorted(matched)

    def is_folder_available(self, crop_folder: str) -> bool:
        """Check if a crop folder was found on disk."""
        return self._folder_paths.get(crop_folder) is not None

    def _get_needed_folders(self, defect_types: set = None) -> set:
        """Determine which unique crop folders are needed."""
        folders = set()
        entries_to_check = CROP_DEFECT_MAP

        if defect_types:
            entries_to_check = {
                k: v for k, v in CROP_DEFECT_MAP.items()
                if k in defect_types
            }

        for defect, entry in entries_to_check.items():
            configs = entry if isinstance(entry, list) else [entry]
            for cfg in configs:
                folders.add(cfg["crop_folder"])

        return folders

    def _resolve_folder(
        self,
        crop_folder: str,
        model_id: str,
        date_str: str,
        drives: List[str],
    ) -> Optional[str]:
        """Find a crop folder across drives, with caching."""
        if crop_folder in self._folder_paths:
            return self._folder_paths[crop_folder]

        path = find_mavin_across_drives(model_id, date_str, crop_folder, drives)
        self._folder_paths[crop_folder] = path
        return path

    def _index_folder(self, crop_folder: str, crop_path: str) -> int:
        """
        Walk the crop folder and index every file by cell_id.

        For folders with class subfolders, walks into each subfolder.
        For flat folders, reads directly.

        Returns total number of files indexed.
        """
        count = 0

        for dirpath, dirnames, filenames in os.walk(crop_path):
            for fname in filenames:
                cell_id = self._extract_cell_id(fname)
                if cell_id:
                    filepath = os.path.join(dirpath, fname)
                    self._file_index[(crop_folder, cell_id)].append(
                        (filepath, fname)
                    )
                    count += 1

        return count

    @staticmethod
    def _extract_cell_id(filename: str) -> Optional[str]:
        """
        Extract the cell_id from a crop image filename.

        Crop filenames start with cell_id followed by underscore:
            a635K06000_03-1_AN_002920_LOWER_1_A_L_...
            a5BFK04508_03-1_AN_001606_UPPER_2_Gap_DL_...

        The cell_id is the first segment before the first underscore.
        """
        if not filename:
            return None
        idx = filename.find("_")
        if idx > 0:
            return filename[:idx]
        return None