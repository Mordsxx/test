import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading, time, os, subprocess, sys

from core.video_analyzer import analyze_video
from core.process_manager import run_patch, run_interpolation

BG = "#080808"
PANEL = "#111111"
CARD = "#151515"
BORDER = "#292929"
FG = "#FFFFFF"
MUTED = "#999999"
ACCENT = "#8B5CF6"
ACCENT_HOVER = "#A78BFA"

class MordsStudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mords Studio")
        self.geometry("1120x740")
        self.minsize(940, 620)
        self.configure(bg=BG)
        self.input_path = None
        self.output_dir = str(Path.home() / "Videos" / "MordsStudio")
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        self._style()
        self._build_shell()
        self.show_dashboard()

    def _style(self):
        s = ttk.Style(self)
        try: s.theme_use("clam")
        except tk.TclError: pass
        s.configure("TProgressbar", troughcolor="#242424", background=ACCENT, bordercolor="#242424", lightcolor=ACCENT, darkcolor=ACCENT)
        s.configure("TCombobox", fieldbackground="#202020", background="#202020", foreground=FG, arrowcolor=FG)
        s.map("TCombobox", fieldbackground=[("readonly", "#202020")], foreground=[("readonly", FG)])

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg="#0D0D0D", width=220, highlightbackground=BORDER, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="MORDS", bg="#0D0D0D", fg=FG, font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=22, pady=(28, 0))
        tk.Label(self.sidebar, text="STUDIO", bg="#0D0D0D", fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(0, 30))
        self._nav("Dashboard", self.show_dashboard)
        self._nav("AI Interpolation", self.show_interpolation)
        self._nav("TikTok 60FPS Patch", self.show_patch)
        self._nav("About", self.show_about)
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=18, pady=22)
        tk.Label(self.sidebar, text="Made by Mords", bg="#0D0D0D", fg=FG, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22)
        tk.Label(self.sidebar, text="TikTok: @Mords_69", bg="#0D0D0D", fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=22, pady=(5, 18))
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

    def _nav(self, label, command):
        b = tk.Button(self.sidebar, text=label, command=command, anchor="w", bg="#0D0D0D", fg="#CFCFCF",
                      activebackground="#1C1728", activeforeground=FG, relief="flat", bd=0,
                      font=("Segoe UI", 10), padx=20, pady=12, cursor="hand2")
        b.pack(fill="x", padx=8, pady=2)

    def _clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def _header(self, title, subtitle):
        tk.Label(self.content, text=title, bg=BG, fg=FG, font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=34, pady=(28, 4))
        tk.Label(self.content, text=subtitle, bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=36, pady=(0, 22))

    def _card(self, parent, title, desc, button_text, command):
        frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(frame, text=title, bg=CARD, fg=FG, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=22, pady=(22, 8))
        tk.Label(frame, text=desc, bg=CARD, fg=MUTED, justify="left", wraplength=340, font=("Segoe UI", 10)).pack(anchor="w", padx=22, pady=(0, 20))
        tk.Button(frame, text=button_text, command=command, bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
                  activeforeground="white", relief="flat", bd=0, padx=18, pady=10, font=("Segoe UI", 9, "bold"), cursor="hand2").pack(anchor="w", padx=22, pady=(0, 22))
        return frame

    def show_dashboard(self):
        self._clear()
        self._header("Mords Studio", "Professional video processing workspace")
        wrap = tk.Frame(self.content, bg=BG)
        wrap.pack(fill="x", padx=34)
        a = self._card(wrap, "AI Frame Interpolation", "Generate new intermediate frames with RIFE to create smoother motion and higher frame rates.", "OPEN INTERPOLATION", self.show_interpolation)
        b = self._card(wrap, "TikTok 60FPS Patch", "Change MP4 playback timing while preserving the original encoded samples. No frame generation or deletion.", "OPEN PATCH WORKSPACE", self.show_patch)
        a.pack(side="left", fill="both", expand=True, padx=(0, 10))
        b.pack(side="left", fill="both", expand=True, padx=(10, 0))
        info = tk.Frame(self.content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        info.pack(fill="x", padx=34, pady=24)
        tk.Label(info, text="WORKFLOW NOTE", bg=PANEL, fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(16, 6))
        tk.Label(info, text="These are two independent processing engines. Choose the workflow that matches your goal.", bg=PANEL, fg=FG, font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(0, 16))
        self._footer()

    def _footer(self):
        tk.Label(self.content, text="Made by Mords  •  TikTok: @Mords_69", bg=BG, fg="#666666", font=("Segoe UI", 9)).pack(side="bottom", pady=16)

    def _workspace_base(self, title, subtitle):
        self._clear()
        self._header(title, subtitle)
        body = tk.Frame(self.content, bg=BG)
        body.pack(fill="both", expand=True, padx=34)
        self._footer()
        return body

    def _select_file(self, label):
        p = filedialog.askopenfilename(title=label, filetypes=[("MP4 video", "*.mp4"), ("All files", "*.*")])
        if p:
            self.input_path = p
            self.file_label.config(text=Path(p).name, fg=FG)
            self._load_info()

    def _load_info(self):
        if not self.input_path: return
        try:
            data = analyze_video(self.input_path)
            lines = [f"Resolution: {data.get('resolution','Unknown')}",
                     f"FPS: {data.get('fps','Unknown')}",
                     f"Duration: {data.get('duration','Unknown')} sec",
                     f"Video: {data.get('video_codec','Unknown')}  |  Audio: {data.get('audio_codec','None')}",
                     f"Frames: {data.get('frames','Unknown')}"]
            self.info_label.config(text="\n".join(lines))
        except Exception as e:
            self.info_label.config(text=f"Could not analyze video: {e}")

    def _file_panel(self, parent):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0, 14))
        tk.Button(row, text="SELECT MP4", command=lambda: self._select_file("Select input MP4"), bg="#242424", fg=FG, relief="flat", padx=16, pady=10).pack(side="left")
        self.file_label = tk.Label(row, text="No video selected", bg=BG, fg=MUTED, font=("Segoe UI", 10))
        self.file_label.pack(side="left", padx=14)

    def _info_panel(self, parent):
        box = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        box.pack(fill="x", pady=8)
        tk.Label(box, text="VIDEO INFORMATION", bg=PANEL, fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 6))
        self.info_label = tk.Label(box, text="Select a video to inspect its properties.", bg=PANEL, fg=MUTED, justify="left", font=("Consolas", 10))
        self.info_label.pack(anchor="w", padx=16, pady=(0, 14))

    def _output_row(self, parent):
        row = tk.Frame(parent, bg=BG); row.pack(fill="x", pady=10)
        tk.Label(row, text="Output folder", bg=BG, fg=MUTED).pack(side="left")
        self.out_label = tk.Label(row, text=self.output_dir, bg=BG, fg=FG); self.out_label.pack(side="left", padx=12)
        tk.Button(row, text="CHANGE", command=self._choose_output, bg="#242424", fg=FG, relief="flat", padx=12, pady=6).pack(side="right")

    def _choose_output(self):
        p = filedialog.askdirectory(initialdir=self.output_dir)
        if p:
            self.output_dir = p
            self.out_label.config(text=p)

    def _progress(self, parent):
        self.status = tk.Label(parent, text="Ready", bg=BG, fg=MUTED, anchor="w")
        self.status.pack(fill="x", pady=(12, 4))
        self.bar = ttk.Progressbar(parent, mode="indeterminate")
        self.bar.pack(fill="x", pady=(0, 10))

    def show_patch(self):
        body = self._workspace_base("TikTok 60FPS Patch", "Modify MP4 playback timing without re-encoding the media streams.")
        self._file_panel(body); self._info_panel(body)
        row = tk.Frame(body, bg=BG); row.pack(fill="x", pady=12)
        tk.Label(row, text="Slowdown multiplier", bg=BG, fg=MUTED).pack(side="left")
        self.patch_factor = ttk.Combobox(row, values=["2x", "3x", "4x"], state="readonly", width=8)
        self.patch_factor.set("2x"); self.patch_factor.pack(side="left", padx=12)
        self._output_row(body); self._progress(body)
        tk.Button(body, text="START PATCH", command=self._start_patch, bg=ACCENT, fg="white", relief="flat", padx=22, pady=12, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=8)

    def _start_patch(self):
        if not self.input_path:
            messagebox.showwarning("Mords Studio", "Select an MP4 file first."); return
        factor = int(self.patch_factor.get().replace("x",""))
        self._run_async(lambda: run_patch(self.input_path, self.output_dir, factor), "Patching MP4 timing...")

    def show_interpolation(self):
        body = self._workspace_base("AI Frame Interpolation", "Generate AI intermediate frames using an external RIFE NCNN Vulkan executable.")
        self._file_panel(body); self._info_panel(body)
        row = tk.Frame(body, bg=BG); row.pack(fill="x", pady=10)
        tk.Label(row, text="Target FPS", bg=BG, fg=MUTED).pack(side="left")
        self.target_fps = ttk.Combobox(row, values=["2x", "3x", "4x"], state="readonly", width=8)
        self.target_fps.set("2x"); self.target_fps.pack(side="left", padx=12)
        tk.Label(row, text="RIFE executable", bg=BG, fg=MUTED).pack(side="left", padx=(28, 8))
        self.rife_path = tk.StringVar()
        tk.Entry(row, textvariable=self.rife_path, width=36, bg="#202020", fg=FG, insertbackground=FG, relief="flat").pack(side="left", ipady=7)
        tk.Button(row, text="BROWSE", command=self._choose_rife, bg="#242424", fg=FG, relief="flat", padx=10, pady=7).pack(side="left", padx=8)
        self._output_row(body); self._progress(body)
        tk.Button(body, text="START INTERPOLATION", command=self._start_interpolation, bg=ACCENT, fg="white", relief="flat", padx=22, pady=12, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=8)
        tk.Label(body, text="Requires FFmpeg and rife-ncnn-vulkan. See README for setup.", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=8)

    def _choose_rife(self):
        p = filedialog.askopenfilename(filetypes=[("RIFE executable", "*.exe"), ("All files", "*.*")])
        if p: self.rife_path.set(p)

    def _start_interpolation(self):
        if not self.input_path:
            messagebox.showwarning("Mords Studio", "Select an MP4 file first."); return
        if not self.rife_path.get() or not Path(self.rife_path.get()).exists():
            messagebox.showwarning("Mords Studio", "Select a valid rife-ncnn-vulkan executable."); return
        multiplier = int(self.target_fps.get().replace("x",""))
        self._run_async(lambda: run_interpolation(self.input_path, self.output_dir, multiplier, self.rife_path.get()), "Running RIFE interpolation...")

    def _run_async(self, fn, message):
        self.status.config(text=message); self.bar.start(12)
        def worker():
            try:
                result = fn()
                self.after(0, lambda: self._finish(True, str(result)))
            except Exception as e:
                self.after(0, lambda: self._finish(False, str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, ok, message):
        self.bar.stop()
        self.status.config(text=("Completed: " if ok else "Error: ") + message, fg=("#9BE7A5" if ok else "#FF7777"))
        if ok: messagebox.showinfo("Mords Studio", message)
        else: messagebox.showerror("Mords Studio", message)

    def show_about(self):
        self._clear(); self._header("About Mords Studio", "Application information and credits")
        box = tk.Frame(self.content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        box.pack(fill="x", padx=34, pady=8)
        for text, color, size, weight in [
            ("MORDS STUDIO", FG, 22, "bold"),
            ("AI Frame Interpolation + MP4 Timing Patch", MUTED, 10, "normal"),
            ("Made by Mords", FG, 13, "bold"),
            ("TikTok: @Mords_69", ACCENT, 11, "bold"),
            ("Version 0.1.0 — Development Build", MUTED, 9, "normal")]:
            tk.Label(box, text=text, bg=CARD, fg=color, font=("Segoe UI", size, weight)).pack(anchor="w", padx=24, pady=8)
        self._footer()
