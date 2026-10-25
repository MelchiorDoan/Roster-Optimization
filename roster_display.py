"""
************************************************************************
  Roster Display — the pop-up window for roster_optimizer.py

  Developed by:
    Doan Nam Khanh

  Shows the finished roster in a clean window:
    - a coloured grid of who works which day (and for how many hours)
    - a coverage row under the grid: green = enough hours, red = short
    - the total weekly labour cost in large type

  This file only DRAWS the results. It does no maths and reads no CSV
  files. roster_optimizer.py does the work and hands the answers over.

  Keep this file in the same folder as roster_optimizer.py.
  It uses tkinter, which comes with a standard Python install, so there is
  nothing extra to install. It needs a screen to draw on, so it will not
  open on a server with no desktop (use --no-popup there).
************************************************************************
"""

# ------------------------------- COLOURS & FONTS -------------------------------
NAVY = "#1F3A5F"       # header bar
NAVY_TEXT = "#DCE6F2"  # lighter text on the header bar
PAGE = "#F4F6F9"       # window background
CARD = "#FFFFFF"       # white cards
INK = "#1B2430"        # main text
MUTED = "#6B7785"      # secondary text
LINE = "#D9DEE5"       # thin dividers
SHIFT_BG = "#D6E8FA"   # a scheduled shift
SHIFT_FG = "#12456E"
OFF_BG = "#F0F2F5"     # a day off
OK_BG, OK_FG = "#DDF3E4", "#17653A"
BAD_BG, BAD_FG = "#FBE0E0", "#9B1C1C"

FONT = "Segoe UI"  # Windows font; other systems quietly substitute their own


def _make_windows_text_sharp():
    """On Windows, stop the window looking blurry on high-resolution screens."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass  # not Windows, or not supported — harmless to skip


def show_roster_window(days, employees, required, scheduled, total_cost):
    """
    Open the roster window and wait until the user closes it.

    days       : list of day names, e.g. ["monday", ..., "sunday"]
    employees  : list of (name, shifts, total_hours) where `shifts` has one
                 entry per day: the hours worked that day, or 0 for a day off
    required   : hours required each day (same order as `days`)
    scheduled  : hours actually scheduled each day (same order as `days`)
    total_cost : the weekly labour cost, in dollars
    """
    import tkinter as tk  # imported here so this file can be loaded even where tkinter is missing

    _make_windows_text_sharp()
    window = tk.Tk()
    window.title("Optimised Roster")
    window.configure(bg=PAGE)
    window.resizable(False, False)

    # ---- Header bar -------------------------------------------------------
    header = tk.Frame(window, bg=NAVY)
    header.pack(fill="x")
    tk.Label(header, text="Optimised Weekly Roster", bg=NAVY, fg="white",
             font=(FONT, 18, "bold")).pack(anchor="w", padx=24, pady=(16, 0))
    tk.Label(header, text="The lowest-cost schedule that covers every day's required hours",
             bg=NAVY, fg=NAVY_TEXT, font=(FONT, 10)).pack(anchor="w", padx=24, pady=(0, 16))

    body = tk.Frame(window, bg=PAGE)
    body.pack(padx=24, pady=18)

    # ---- Total cost card --------------------------------------------------
    cost_card = tk.Frame(body, bg=CARD, highlightbackground=LINE, highlightthickness=1)
    cost_card.pack(fill="x", pady=(0, 16))
    tk.Label(cost_card, text="TOTAL WEEKLY LABOUR COST", bg=CARD, fg=MUTED,
             font=(FONT, 9, "bold")).pack(anchor="w", padx=18, pady=(12, 0))
    tk.Label(cost_card, text=f"${total_cost:,.2f}", bg=CARD, fg=INK,
             font=(FONT, 28, "bold")).pack(anchor="w", padx=18, pady=(0, 12))

    # ---- Roster grid ------------------------------------------------------
    grid_card = tk.Frame(body, bg=CARD, highlightbackground=LINE, highlightthickness=1)
    grid_card.pack(fill="x")
    grid = tk.Frame(grid_card, bg=CARD)
    grid.pack(padx=14, pady=14)

    def cell(row, col, text, bg=CARD, fg=INK, bold=False, anchor="center", width=9):
        tk.Label(grid, text=text, bg=bg, fg=fg, width=width, anchor=anchor,
                 font=(FONT, 10, "bold" if bold else "normal"),
                 pady=7).grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

    # column headings
    cell(0, 0, "Employee", fg=MUTED, bold=True, anchor="w", width=14)
    for j, day in enumerate(days):
        cell(0, j + 1, day[:3].upper(), fg=MUTED, bold=True)
    cell(0, len(days) + 1, "WEEK", fg=MUTED, bold=True)

    # one row per employee
    for i, (name, shifts, total_hours) in enumerate(employees, start=1):
        cell(i, 0, name.replace("_", " "), bold=True, anchor="w", width=14)
        for j, h in enumerate(shifts):
            if h > 0:
                cell(i, j + 1, f"{h:g}h", bg=SHIFT_BG, fg=SHIFT_FG, bold=True)
            else:
                cell(i, j + 1, "off", bg=OFF_BG, fg=MUTED)
        cell(i, len(days) + 1, f"{total_hours:g}h", bold=True)

    # divider, then the coverage check rows
    base = len(employees) + 1
    tk.Frame(grid, bg=LINE, height=2).grid(row=base, column=0, columnspan=len(days) + 2,
                                           sticky="ew", pady=6)
    cell(base + 1, 0, "Hours needed", fg=MUTED, anchor="w", width=14)
    cell(base + 2, 0, "Hours rostered", fg=MUTED, anchor="w", width=14)
    cell(base + 3, 0, "Covered?", bold=True, anchor="w", width=14)
    for j in range(len(days)):
        met = scheduled[j] >= required[j]
        cell(base + 1, j + 1, f"{required[j]:g}h", fg=MUTED)
        cell(base + 2, j + 1, f"{scheduled[j]:g}h")
        cell(base + 3, j + 1, "Yes" if met else "SHORT", bold=True,
             bg=OK_BG if met else BAD_BG, fg=OK_FG if met else BAD_FG)

    # ---- Note + Close button ---------------------------------------------
    tk.Label(body, text="A day can be rostered a little over its need, because each person "
                        "works their whole listed shift.",
             bg=PAGE, fg=MUTED, font=(FONT, 9), wraplength=700,
             justify="left").pack(anchor="w", pady=(12, 0))

    close = tk.Button(window, text="Close", command=window.destroy, bg=NAVY, fg="white",
                      activebackground="#2B4F7E", activeforeground="white",
                      font=(FONT, 11, "bold"), relief="flat", padx=30, pady=8, cursor="hand2")
    close.pack(pady=(0, 20))
    window.bind("<Escape>", lambda event: window.destroy())  # Esc also closes it

    # ---- Centre on screen and bring to the front -------------------------
    window.update_idletasks()
    x = (window.winfo_screenwidth() - window.winfo_width()) // 2
    y = (window.winfo_screenheight() - window.winfo_height()) // 3
    window.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    window.lift()
    window.attributes("-topmost", True)                     # jump above other windows...
    window.after(300, lambda: window.attributes("-topmost", False))  # ...then behave normally
    window.focus_force()

    window.mainloop()
