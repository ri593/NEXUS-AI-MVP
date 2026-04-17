import json
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import simpledialog
from pathlib import Path
from typing import Callable


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE = CONFIG_DIR / "api_keys.json"

SYSTEM_NAME = "NEXUS AI"
MODEL_BADGE = "TEROSICA GEN-1"

C_BG = "#060b15"
C_TEXT = "#edf3ff"
C_SUB = "#91a0bf"
C_ACCENT = "#8fd4ff"
C_SIDEBAR = "#060a12"
C_PANEL = "#111a2b"
C_PANEL_2 = "#15233a"


class TEROSICAUI:
    def __init__(self, face_path=None, size=None):
        self.root = tk.Tk()
        self.root.title(f"{SYSTEM_NAME} - {MODEL_BADGE}")
        self.root.configure(bg=C_BG)
        self.root.minsize(980, 620)

        self.W = 1200
        self.H = 760
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{self.W}x{self.H}+{(sw - self.W)//2}+{(sh - self.H)//2}")

        self.speaking = False
        self.muted = False
        self.status_text = "INITIALISING"
        self._assistant_state = "INITIALISING"
        self.on_text_command: Callable[[str], None] | None = None
        self._api_key_ready = self._api_keys_exist()

        self._orbs = [
            {"x": 350.0, "y": 180.0, "r": 320, "dx": 0.52, "dy": 0.24, "c": "#0a3c7a", "stipple": "gray50"},
            {"x": 820.0, "y": 440.0, "r": 390, "dx": -0.42, "dy": 0.32, "c": "#113e71", "stipple": "gray25"},
            {"x": 620.0, "y": 640.0, "r": 300, "dx": 0.36, "dy": -0.28, "c": "#06284f", "stipple": "gray50"},
        ]
        self._pulse = 0.0

        self.bg_canvas = tk.Canvas(self.root, width=self.W, height=self.H, bg=C_BG, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0)

        self._build_phone_shell()
        self._draw_background()
        self._set_state_visuals()

        if not self._api_key_ready:
            self._show_setup_ui()

        self.root.bind("<F4>", lambda e: self._toggle_mute())
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        self._animate()

    def _build_phone_shell(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(
            self.root,
            bg=C_SIDEBAR,
            highlightthickness=1,
            highlightbackground="#101a2e",
            bd=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.configure(width=250)
        self.sidebar.grid_propagate(False)

        self.main_panel = tk.Frame(self.root, bg=C_BG, bd=0)
        self.main_panel.grid(row=0, column=1, sticky="nsew")
        self.main_panel.grid_rowconfigure(1, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_panel()

    def _build_sidebar(self):
        tk.Label(
            self.sidebar,
            text="NEXUS AI",
            fg=C_TEXT,
            bg=C_SIDEBAR,
            font=("Bahnschrift", 18, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(18, 12))

        search_box = tk.Frame(
            self.sidebar,
            bg="#0f1625",
            highlightthickness=1,
            highlightbackground="#1f2d47",
        )
        search_box.pack(fill="x", padx=12, pady=(0, 16))
        self._sidebar_search = tk.Entry(
            search_box,
            bg="#0f1625",
            fg="#9fb3d9",
            insertbackground=C_TEXT,
            relief="flat",
            font=("Segoe UI", 10),
        )
        self._sidebar_search.insert(0, "Search chats")
        self._sidebar_search.pack(fill="x", padx=10, pady=9)

        self._make_sidebar_action("Libraries", lambda: self.write_log("SYS: Libraries panel coming soon."))
        self._make_sidebar_action("Explore GPTs", lambda: self.write_log("SYS: Explore GPTs panel coming soon."))
        self._make_sidebar_action("Settings", self._show_settings_hint)

        tk.Label(
            self.sidebar,
            text="Chats",
            fg="#69cfff",
            bg=C_SIDEBAR,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(18, 6))

        self._make_sidebar_chat("Draft an email regarding...")
        self._make_sidebar_chat("Help me draft an ...")

        quick_label = tk.Label(
            self.sidebar,
            text="Quick Actions",
            fg=C_SUB,
            bg=C_SIDEBAR,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        quick_label.pack(fill="x", padx=14, pady=(18, 8))

        quick_row = tk.Frame(self.sidebar, bg=C_SIDEBAR)
        quick_row.pack(fill="x", padx=12)
        self._make_quick_btn(quick_row, "Open App", self._open_app_control).pack(side="left", padx=(0, 6))
        self._make_quick_btn(quick_row, "Browser", self._browser_control).pack(side="left", padx=(0, 6))
        self._make_quick_btn(quick_row, "PC", self._pc_control).pack(side="left")

        bottom = tk.Frame(self.sidebar, bg=C_SIDEBAR)
        bottom.pack(side="bottom", fill="x", padx=14, pady=14)
        tk.Label(bottom, text="kamal Manocha", fg=C_TEXT, bg=C_SIDEBAR, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(bottom, text="kamalmanocha@gmail.com", fg=C_SUB, bg=C_SIDEBAR, font=("Segoe UI", 8)).pack(anchor="w")

    def _build_main_panel(self):
        top_row = tk.Frame(self.main_panel, bg=C_BG)
        top_row.grid(row=0, column=0, sticky="ew", padx=22, pady=(16, 0))
        top_row.grid_columnconfigure(0, weight=1)

        tk.Label(
            top_row,
            text=MODEL_BADGE,
            fg=C_SUB,
            bg=C_BG,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="w")

        self.status_chip = tk.Label(
            top_row,
            text="INITIALISING",
            fg=C_TEXT,
            bg="#20324f",
            font=("Segoe UI", 8, "bold"),
            padx=12,
            pady=4,
        )
        self.status_chip.grid(row=0, column=1, sticky="e")

        center_wrap = tk.Frame(self.main_panel, bg=C_BG)
        center_wrap.grid(row=1, column=0, sticky="nsew", padx=22)
        center_wrap.grid_columnconfigure(0, weight=1)
        center_wrap.grid_rowconfigure(0, weight=1)
        center_wrap.grid_rowconfigure(2, weight=1)

        prompt_block = tk.Frame(center_wrap, bg=C_BG)
        prompt_block.grid(row=1, column=0, sticky="ew")
        prompt_block.grid_columnconfigure(0, weight=1)

        self.hero_title = tk.Label(
            prompt_block,
            text="What's On Your Mind Today ?",
            fg=C_TEXT,
            bg=C_BG,
            font=("Cambria", 28, "normal"),
        )
        self.hero_title.grid(row=0, column=0, pady=(10, 26))

        input_wrap = tk.Frame(
            prompt_block,
            bg=C_PANEL_2,
            highlightthickness=1,
            highlightbackground="#355178",
        )
        input_wrap.grid(row=1, column=0, sticky="ew")
        input_wrap.grid_columnconfigure(0, weight=1)

        self._input_var = tk.StringVar()
        self._input_entry = tk.Entry(
            input_wrap,
            textvariable=self._input_var,
            bg=C_PANEL_2,
            fg=C_TEXT,
            insertbackground=C_TEXT,
            relief="flat",
            font=("Segoe UI", 12),
        )
        self._input_entry.grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=12)
        self._input_entry.insert(0, "Ask Me Anything ?")
        self._input_entry.bind("<FocusIn>", self._on_input_focus)
        self._input_entry.bind("<Return>", self._on_input_submit)
        self._input_entry.bind("<KP_Enter>", self._on_input_submit)

        send_btn = tk.Button(
            input_wrap,
            text="Send",
            command=self._on_input_submit,
            bg="#223652",
            fg="#d7ecff",
            activebackground="#2c456a",
            activeforeground=C_TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            cursor="hand2",
        )
        send_btn.grid(row=0, column=1, padx=(4, 8), pady=7)

        self.mic_btn = tk.Label(
            input_wrap,
            text="MIC",
            fg="#d7ecff",
            bg="#223652",
            font=("Segoe UI Symbol", 11, "bold"),
            padx=10,
            pady=7,
        )
        self.mic_btn.grid(row=0, column=2, padx=(2, 4), pady=7)

        self.send_icon_btn = tk.Button(
            input_wrap,
            text=">",
            command=self._on_input_submit,
            bg="#223652",
            fg="#d7ecff",
            activebackground="#2c456a",
            activeforeground=C_TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI Symbol", 11, "bold"),
            padx=10,
            pady=7,
            cursor="hand2",
        )
        self.send_icon_btn.grid(row=0, column=3, padx=(2, 10), pady=7)

        self.upgrade_btn = tk.Button(
            prompt_block,
            text="Upgrade to Pro",
            command=lambda: self.write_log("SYS: Upgrade page coming soon."),
            bg="#e7ecf3",
            fg="#202226",
            activebackground="#f4f6fb",
            activeforeground="#111",
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 10),
            padx=16,
            pady=7,
        )
        self.upgrade_btn.grid(row=2, column=0, pady=(22, 0))

        log_wrap = tk.Frame(self.main_panel, bg=C_BG, highlightthickness=0)
        log_wrap.grid(row=2, column=0, sticky="ew", padx=22, pady=(8, 16))

        self.log_text = tk.Text(
            log_wrap,
            bg=C_PANEL,
            fg=C_TEXT,
            insertbackground=C_TEXT,
            relief="flat",
            borderwidth=0,
            wrap="word",
            padx=14,
            pady=10,
            height=8,
            font=("Consolas", 10),
            highlightthickness=1,
            highlightbackground="#2a3e60",
        )
        self.log_text.pack(fill="x")
        self.log_text.configure(state="disabled")
        self.log_text.tag_config("you", foreground="#d8e2ff")
        self.log_text.tag_config("ai", foreground="#8fd4ff")
        self.log_text.tag_config("sys", foreground="#b8c4e2")
        self.log_text.tag_config("err", foreground="#ff7b92")

        controls = tk.Frame(self.main_panel, bg=C_BG)
        controls.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 14))

        self.mute_btn = tk.Button(
            controls,
            text="Mute",
            command=self._toggle_mute,
            bg="#142235",
            fg=C_SUB,
            activebackground="#213752",
            activeforeground=C_TEXT,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
        )
        self.mute_btn.pack(side="left")

    def _make_sidebar_action(self, text: str, command):
        btn = tk.Button(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            bg=C_SIDEBAR,
            fg="#d4def7",
            activebackground="#111c2f",
            activeforeground=C_TEXT,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 10),
            padx=12,
            pady=8,
        )
        btn.pack(fill="x", padx=10, pady=1)

    def _make_sidebar_chat(self, text: str):
        btn = tk.Button(
            self.sidebar,
            text=text,
            command=lambda t=text: self.write_log(f"SYS: Opened chat - {t}"),
            anchor="w",
            bg="#07101d",
            fg="#a9badc",
            activebackground="#0f1a2d",
            activeforeground=C_TEXT,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 9),
            padx=10,
            pady=7,
        )
        btn.pack(fill="x", padx=10, pady=2)

    def _show_settings_hint(self):
        self.write_log("SYS: Settings are managed via config/api_keys.json.")

    def _make_quick_btn(self, parent, label: str, command):
        return tk.Button(
            parent,
            text=label,
            command=command,
            bg="#16253b",
            fg=C_ACCENT,
            activebackground="#213754",
            activeforeground=C_TEXT,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=7,
        )

    def _dispatch_text_command(self, text: str):
        text = (text or "").strip()
        if not text:
            return
        self.write_log(f"You: {text}")
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    def _open_app_control(self):
        app_name = simpledialog.askstring("Open App", "App name to open (e.g. Chrome, Spotify):", parent=self.root)
        if not app_name:
            return
        self._dispatch_text_command(f"Open {app_name}.")

    def _browser_control(self):
        query = simpledialog.askstring("Browser Control", "Website or search query:", parent=self.root)
        if not query:
            return
        self._dispatch_text_command(f"Use browser control to open and handle: {query}")

    def _pc_control(self):
        task = simpledialog.askstring("PC Control", "What should I do on your PC?", parent=self.root)
        if not task:
            return
        self._dispatch_text_command(f"Use computer control: {task}")

    def _draw_background(self):
        self.bg_canvas.delete("all")
        self.bg_canvas.create_rectangle(0, 0, self.W, self.H, fill=C_BG, outline="")

        # Layered soft glows create the deep blue motion background from the reference design.
        for orb in self._orbs:
            x, y, r = orb["x"], orb["y"], orb["r"]
            color = orb["c"]
            stipple = orb.get("stipple", "gray25")
            self.bg_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="", stipple=stipple)
            self.bg_canvas.create_oval(
                x - int(r * 0.72),
                y - int(r * 0.72),
                x + int(r * 0.72),
                y + int(r * 0.72),
                fill=color,
                outline="",
                stipple="gray50",
            )

        sidebar_glow = int(70 + 16 * (1 + self._pulse))
        self.bg_canvas.create_rectangle(0, 0, 260, self.H, fill="#04080f", outline="")
        self.bg_canvas.create_rectangle(258, 0, 264, self.H, fill="#1f3559", outline="")
        self.bg_canvas.create_rectangle(260, 0, self.W, sidebar_glow, fill="#112341", outline="")
        self.bg_canvas.tag_lower("all")

    def _animate(self):
        self._pulse += 0.09

        for orb in self._orbs:
            orb["x"] += orb["dx"]
            orb["y"] += orb["dy"]
            if orb["x"] < -120 or orb["x"] > self.W + 120:
                orb["dx"] *= -1
            if orb["y"] < -120 or orb["y"] > self.H + 120:
                orb["dy"] *= -1
            if random.random() < 0.01:
                orb["dx"] += random.uniform(-0.05, 0.05)
                orb["dy"] += random.uniform(-0.05, 0.05)

        self._draw_background()
        self.root.after(50, self._animate)

    def _on_input_submit(self, event=None):
        text = self._input_var.get().strip()
        if not text or text == "Ask Me Anything ?":
            return
        self._input_var.set("")
        self._dispatch_text_command(text)

    def _on_input_focus(self, event=None):
        if self._input_var.get().strip() == "Ask Me Anything ?":
            self._input_var.set("")

    def _toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.set_state("MUTED")
            self.write_log("SYS: Microphone muted.")
        else:
            self.set_state("LISTENING")
            self.write_log("SYS: Microphone active.")

    def set_state(self, state: str):
        self._assistant_state = state
        if state == "MUTED":
            self.speaking = False
            self.status_text = "MUTED"
        elif state == "SPEAKING":
            self.speaking = True
            self.status_text = "SPEAKING"
        elif state == "THINKING":
            self.speaking = False
            self.status_text = "THINKING"
        elif state == "PROCESSING":
            self.speaking = False
            self.status_text = "PROCESSING"
        elif state == "LISTENING":
            self.speaking = False
            self.status_text = "LISTENING"
        else:
            self.speaking = False
            self.status_text = "ONLINE"
        self._set_state_visuals()

    def _set_state_visuals(self):
        if self.muted or self.status_text == "MUTED":
            self.status_chip.configure(text="MUTED", bg="#4a1a2a", fg="#ff9db0")
            self.mute_btn.configure(text="Unmute", fg="#ff9db0")
            self.mic_btn.configure(bg="#3b1a2a", fg="#ff9db0")
        elif self.status_text == "SPEAKING":
            self.status_chip.configure(text="SPEAKING", bg="#3a2f58", fg="#c9b5ff")
            self.mute_btn.configure(text="Mute", fg=C_SUB)
            self.mic_btn.configure(bg="#3a2f58", fg="#e6dcff")
        elif self.status_text == "THINKING":
            self.status_chip.configure(text="THINKING", bg="#3d3220", fg="#ffd083")
            self.mute_btn.configure(text="Mute", fg=C_SUB)
            self.mic_btn.configure(bg="#2f2a22", fg="#ffd083")
        else:
            self.status_chip.configure(text=self.status_text, bg="#1f3859", fg="#9df0ff")
            self.mute_btn.configure(text="Mute", fg=C_SUB)
            self.mic_btn.configure(bg="#223652", fg=C_TEXT)

    def write_log(self, text: str):
        tl = text.lower()
        if tl.startswith("you:"):
            tag = "you"
            self.set_state("PROCESSING")
        elif tl.startswith("nexus ai:") or tl.startswith("ai:"):
            tag = "ai"
            self.set_state("SPEAKING")
        elif tl.startswith("err:") or "failed" in tl or "error" in tl:
            tag = "err"
        else:
            tag = "sys"

        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text + "\n\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

        if tag == "ai" and not self.muted:
            self.root.after(900, lambda: self.set_state("LISTENING"))

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if not self.muted:
            self.set_state("LISTENING")

    def _api_keys_exist(self) -> bool:
        return API_FILE.exists()

    def wait_for_api_key(self):
        while not self._api_key_ready:
            time.sleep(0.1)

    def _show_setup_ui(self):
        self.setup_frame = tk.Frame(
            self.main_panel,
            bg="#0c1424",
            highlightthickness=1,
            highlightbackground="#31486e",
            bd=0,
        )
        self.setup_frame.place(relx=0.5, rely=0.5, anchor="center", width=380, height=280)

        tk.Label(
            self.setup_frame,
            text="Initialize TEROSICA",
            fg=C_TEXT,
            bg="#0c1424",
            font=("Segoe UI Semibold", 14, "bold"),
        ).pack(pady=(18, 8))

        tk.Label(
            self.setup_frame,
            text="Enter your Gemini API key",
            fg=C_SUB,
            bg="#0c1424",
            font=("Segoe UI", 9),
        ).pack()

        self.gemini_entry = tk.Entry(
            self.setup_frame,
            fg=C_TEXT,
            bg="#101b30",
            insertbackground=C_TEXT,
            relief="flat",
            font=("Segoe UI", 10),
            width=36,
            show="*",
        )
        self.gemini_entry.pack(pady=(14, 10), ipady=6)

        tk.Button(
            self.setup_frame,
            text="Save and Start",
            command=self._save_api_keys,
            bg="#1f3458",
            fg=C_ACCENT,
            activebackground="#2b4676",
            activeforeground=C_TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=8,
            cursor="hand2",
        ).pack(pady=(4, 0))

    def _save_api_keys(self):
        gemini = self.gemini_entry.get().strip()
        if not gemini:
            return
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(API_FILE, "w", encoding="utf-8") as f:
            json.dump({"gemini_api_key": gemini}, f, indent=4)
        self.setup_frame.destroy()
        self._api_key_ready = True
        self.set_state("LISTENING")
        self.write_log("SYS: Systems initialized. NEXUS AI online.")


NexusAIUI = TEROSICAUI
