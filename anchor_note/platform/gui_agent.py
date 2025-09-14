"""
GUI agent (Tkinter) — minimal, cross-platform GUI that displays checklist and allows marking done.

This file is intentionally simple so it works without heavy GUI dependencies. If you prefer PySide6
or PyQt, swap the implementation (the repo also has PySide sketches elsewhere).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone
from ..core.checklist import list_pending_tasks, mark_task_done

def _format_dt(dt):
    return dt.strftime("%Y-%m-%d %H:%M") if dt else ""

class ChecklistWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sticky Remind — Checklist")
        self.geometry("520x620")
        self._build_ui()
        self.refresh_tasks()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        hdr = ttk.Label(frame, text="Sticky Remind — Checklist", font=("Helvetica", 14, "bold"))
        hdr.pack(pady=6)
        self.tree = ttk.Treeview(frame, columns=("due", "red", "title"), show="headings", selectmode="browse")
        self.tree.heading("due", text="Due")
        self.tree.heading("red", text="Red")
        self.tree.heading("title", text="Title")
        self.tree.column("title", width=300)
        self.tree.pack(fill=tk.BOTH, expand=True)
        btnframe = ttk.Frame(frame)
        btnframe.pack(fill=tk.X, pady=8)
        ttk.Button(btnframe, text="Refresh", command=self.refresh_tasks).pack(side=tk.LEFT, padx=4)
        ttk.Button(btnframe, text="Mark Done", command=self.mark_done).pack(side=tk.LEFT, padx=4)
        ttk.Button(btnframe, text="Dismiss Alerts", command=self.dismiss_alerts).pack(side=tk.RIGHT, padx=4)

    def refresh_tasks(self):
        self.tree.delete(*self.tree.get_children())
        rows = list_pending_tasks()
        for t in rows:
            due = _format_dt(t["end"])
            self.tree.insert("", tk.END, iid=str(t["id"]), values=(due, "YES" if t["red"] else "", t["title"]))

    def mark_done(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a task first.")
            return
        task_id = int(sel[0])
        mark_task_done(task_id)
        self.refresh_tasks()

    def dismiss_alerts(self):
        # For minimal implementation, "dismiss" equals mark done for red tasks in the list
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            if vals[1] == "YES":
                mark_task_done(int(iid))
        self.refresh_tasks()

def main():
    app = ChecklistWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
