from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from fetcher import normalize_cell_ids, copy_flowmaps


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Flowmap Fetcher")
        self.geometry("880x620")

        self.date_var = tk.StringVar(value="2026-02-22")
        self.output_var = tk.StringVar(value=r"D:\OUTPUT")

        self._build()

    def _build(self):
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.date_var, width=18).grid(row=0, column=1, sticky="w", padx=(8, 20))

        ttk.Label(top, text="Output folder:").grid(row=0, column=2, sticky="w")
        ttk.Entry(top, textvariable=self.output_var, width=40).grid(row=0, column=3, sticky="w", padx=(8, 0))

        mid = ttk.Frame(self, padding=(12, 0, 12, 12))
        mid.pack(fill="both", expand=True)

        ttk.Label(mid, text="Paste Cell IDs (one per line, or separated by spaces/commas):").pack(anchor="w")

        self.cell_text = tk.Text(mid, height=12, wrap="word")
        self.cell_text.pack(fill="x", pady=(6, 10))
        self.cell_text.insert("1.0", "d62MJ74960\ng62MJ17753\nd62MJ72378")

        btn_row = ttk.Frame(mid)
        btn_row.pack(fill="x")

        self.run_btn = ttk.Button(btn_row, text="Fetch Flowmaps", command=self.on_run)
        self.run_btn.pack(side="left")

        self.status_lbl = ttk.Label(btn_row, text="")
        self.status_lbl.pack(side="left", padx=12)

        ttk.Label(mid, text="Log:").pack(anchor="w", pady=(12, 0))
        self.log = tk.Text(mid, height=18, wrap="word")
        self.log.pack(fill="both", expand=True, pady=(6, 0))
        self._log_line("Ready.")

    def _log_line(self, s: str):
        self.log.insert("end", s + "\n")
        self.log.see("end")

    def on_run(self):
        date_str = self.date_var.get().strip()
        raw_cells = self.cell_text.get("1.0", "end").strip()
        output_root = Path(self.output_var.get().strip())

        cell_ids = normalize_cell_ids(raw_cells)
        if not cell_ids:
            messagebox.showerror("No Cell IDs", "Please paste at least one Cell ID.")
            return

        self.run_btn.configure(state="disabled")
        self.status_lbl.configure(text="Running...")

        try:
            results, summary = copy_flowmaps(
                date_str=date_str,
                cell_ids=cell_ids,
                f_root=Path(r"F:\Files"),
                output_root=output_root,
            )

            self._log_line("")
            self._log_line(f"Date: {date_str}")
            self._log_line(f"Output: {output_root}")
            self._log_line(f"Cells total: {summary['cells_total']}")
            self._log_line(f"Cells OK: {summary['cells_ok']}")
            self._log_line(f"Cells missing: {summary['cells_missing']}")
            self._log_line(f"Images copied: {summary['images_copied']}")
            self._log_line("-" * 60)

            for r in results:
                self._log_line(f"{r.cell_id} -> {r.message}")
                for p in r.copied_to:
                    self._log_line(f"   copied: {p}")

            messagebox.showinfo("Done", f"Copied {summary['images_copied']} images.\nSaved under:\n{output_root}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log_line(f"[ERROR] {e}")

        finally:
            self.run_btn.configure(state="normal")
            self.status_lbl.configure(text="")



if __name__ == "__main__":
    App().mainloop()