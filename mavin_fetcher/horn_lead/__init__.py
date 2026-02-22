"""
HORN/LEAD (Hornmark + Leadedge) fetch pipeline.

This pipeline is CSV-driven (JUDGE-DEFECT) rather than directory-driven (Crop_A/Crop_B).
It is intentionally isolated from existing A/B area code paths to avoid regressions.
"""