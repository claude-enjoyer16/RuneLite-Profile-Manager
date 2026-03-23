"""Main application window for RuneLite Profile Manager."""

import tkinter as tk
import tkinter.font
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

from src.utils.paths import get_default_profiles2_dir, validate_runelite_folder

import sys

def _get_assets_dir() -> Path:
    """Return the assets directory, handling PyInstaller bundles."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).resolve().parent.parent.parent / "assets"

ASSETS_DIR = _get_assets_dir()
from src.core.profiles import load_profiles, delete_profile, duplicate_profile
from src.core.backup import create_backup
from src.core.cleanup import find_orphaned_files, delete_orphaned_files


class ProfileManagerApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("RuneLite Profile Manager")
        self.geometry("690x800")
        self.minsize(565, 375)

        # Scale all UI elements by 1.25x.
        default_font = tk.font.nametofont("TkDefaultFont")
        default_font.configure(size=int(default_font.cget("size") * 1.25))
        text_font = tk.font.nametofont("TkTextFont")
        text_font.configure(size=int(text_font.cget("size") * 1.25))

        self._apply_dark_theme()

        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.is_file():
            self._icon = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, self._icon)

        self._profiles2_dir = None
        self._profiles: list[dict] = []

        self._build_ui()
        self._try_auto_detect()

    def _apply_dark_theme(self):
        """Apply a Discord Onyx-style dark theme."""
        # Core palette
        bg = "#1e1f22"         # main background
        bg_secondary = "#2b2d31"  # panels, frames
        bg_tertiary = "#232428"   # input fields, treeview
        fg = "#dbdee1"         # primary text
        fg_muted = "#949ba4"   # secondary text
        accent = "#5865f2"     # blurple accent
        accent_hover = "#4752c4"
        danger = "#da373c"     # red for delete/banner
        border = "#3f4147"

        self.configure(bg=bg)

        style = ttk.Style()
        style.theme_use("clam")

        # General
        style.configure(".", background=bg, foreground=fg, borderwidth=0,
                         fieldbackground=bg_tertiary, troughcolor=bg_secondary)
        style.map(".", foreground=[("disabled", fg_muted)])

        # Frames
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)

        # Treeview
        style.configure("Treeview",
                         background=bg_tertiary,
                         foreground=fg,
                         fieldbackground=bg_tertiary,
                         rowheight=30,
                         borderwidth=0)
        style.configure("Treeview.Heading",
                         background=bg_secondary,
                         foreground=fg_muted,
                         borderwidth=1,
                         relief="flat")
        style.map("Treeview",
                   background=[("selected", accent)],
                   foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading",
                   background=[("active", border)])

        # Buttons
        style.configure("TButton",
                         background=bg_secondary,
                         foreground=fg,
                         borderwidth=1,
                         padding=(10, 5),
                         relief="flat")
        style.map("TButton",
                   background=[("active", border), ("disabled", bg)],
                   foreground=[("disabled", fg_muted)])

        # Scrollbar
        style.configure("Vertical.TScrollbar",
                         background=bg_secondary,
                         troughcolor=bg_tertiary,
                         borderwidth=0,
                         arrowsize=0)
        style.map("Vertical.TScrollbar",
                   background=[("active", border)])

    def _build_ui(self):
        """Construct all UI widgets."""
        # -- Warning banner --
        banner = tk.Label(
            self,
            text="⚠ Back up your .runelite/profiles2 before making changes!",
            bg="#da373c",
            fg="#ffffff",
            font=("TkDefaultFont", 12, "bold"),
            pady=6,
        )
        banner.pack(fill=tk.X)

        # -- Folder label --
        self._folder_label = ttk.Label(
            self, text="No profiles folder selected", padding=(10, 8),
        )
        self._folder_label.pack(fill=tk.X)

        # -- Middle section: profile list + action buttons --
        middle = ttk.Frame(self, padding=10)
        middle.pack(fill=tk.BOTH, expand=True)

        # Profile list (left)
        list_frame = ttk.Frame(middle)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tree = ttk.Treeview(
            list_frame, columns=("name",), show="headings", selectmode="browse",
        )
        self._tree.heading("name", text="Profile Name")
        self._tree.column("name", stretch=True)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self._tree.yview,
        )
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.bind("<<TreeviewSelect>>", self._on_selection_change)
        self._tree.bind("<Delete>", lambda _: self._on_delete())

        # Action buttons (right)
        btn_frame = ttk.Frame(middle, padding=(10, 0, 0, 0))
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self._btn_duplicate = ttk.Button(
            btn_frame, text="Duplicate", command=self._on_duplicate, state=tk.DISABLED,
        )
        self._btn_duplicate.pack(fill=tk.X, pady=(0, 5))

        self._btn_delete = ttk.Button(
            btn_frame, text="Delete", command=self._on_delete, state=tk.DISABLED,
        )
        self._btn_delete.pack(fill=tk.X)

        # -- Bottom bar --
        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill=tk.X)

        ttk.Button(
            bottom, text="Select Folder", command=self._on_select_folder,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            bottom, text="Backup", command=self._on_backup,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            bottom, text="Cleanup", command=self._on_cleanup,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            bottom, text="Exit", command=self.destroy,
        ).pack(side=tk.RIGHT)

    # -- Data loading --

    def _try_auto_detect(self):
        """Attempt to auto-detect the default profiles2 directory."""
        default = get_default_profiles2_dir()
        if default:
            self._load_folder(default)

    def _load_folder(self, profiles2_dir):
        """Load profiles from a profiles2 directory."""
        self._profiles2_dir = profiles2_dir
        self._folder_label.config(text=f"Current folder: {profiles2_dir}")
        self.refresh_list()

    def refresh_list(self):
        """Re-read profiles.json from disk and repopulate the treeview."""
        self._tree.delete(*self._tree.get_children())
        self._profiles = []

        if not self._profiles2_dir:
            return

        try:
            self._profiles = load_profiles(self._profiles2_dir)
        except (ValueError, OSError) as e:
            messagebox.showerror("Error", f"Failed to load profiles:\n{e}")
            return

        for profile in self._profiles:
            self._tree.insert("", tk.END, iid=str(profile["id"]), values=(profile["name"],))

        self._update_button_states()

    # -- Selection --

    def _on_selection_change(self, _event=None):
        self._update_button_states()

    def _update_button_states(self):
        """Enable/disable Duplicate and Delete based on selection."""
        selected = self._tree.selection()
        state = tk.NORMAL if selected else tk.DISABLED
        self._btn_duplicate.config(state=state)
        self._btn_delete.config(state=state)

    def _get_selected_profile(self) -> dict | None:
        """Return the currently selected profile dict, or None."""
        selection = self._tree.selection()
        if not selection:
            return None
        selected_id = int(selection[0])
        return next((p for p in self._profiles if p["id"] == selected_id), None)

    # -- Button callbacks --

    def _on_select_folder(self):
        folder = filedialog.askdirectory(title="Select .runelite folder")
        if not folder:
            return

        from pathlib import Path
        try:
            profiles2 = validate_runelite_folder(Path(folder))
        except ValueError as e:
            messagebox.showerror("Invalid Folder", str(e))
            return

        self._load_folder(profiles2)

    def _on_duplicate(self):
        profile = self._get_selected_profile()
        if not profile:
            return

        try:
            new_profile = duplicate_profile(self._profiles2_dir, profile)
        except (ValueError, OSError) as e:
            messagebox.showerror("Error", f"Failed to duplicate profile:\n{e}")
            return

        self.refresh_list()

        # Re-select the original profile.
        iid = str(profile["id"])
        if self._tree.exists(iid):
            self._tree.selection_set(iid)
            self._tree.see(iid)

    def _on_delete(self):
        profile = self._get_selected_profile()
        if not profile:
            return

        # Remember the row index before deleting.
        children = self._tree.get_children()
        idx = list(children).index(str(profile["id"]))

        try:
            delete_profile(self._profiles2_dir, profile)
        except (ValueError, OSError) as e:
            messagebox.showerror("Error", f"Failed to delete profile:\n{e}")
            return

        self.refresh_list()

        # Re-select the item now occupying that row (or the last row).
        children = self._tree.get_children()
        if children:
            select_idx = min(idx, len(children) - 1)
            self._tree.selection_set(children[select_idx])
            self._tree.see(children[select_idx])

    def _on_backup(self):
        if not self._profiles2_dir:
            messagebox.showerror("Error", "No profiles folder selected.")
            return

        try:
            backup_dir = create_backup(self._profiles2_dir)
        except OSError as e:
            messagebox.showerror("Error", f"Failed to create backup:\n{e}")
            return

        messagebox.showinfo(
            "Backup Successful",
            f"Backup created:\n{backup_dir.name}",
        )

    def _on_cleanup(self):
        if not self._profiles2_dir:
            messagebox.showerror("Error", "No profiles folder selected.")
            return

        try:
            orphaned = find_orphaned_files(self._profiles2_dir)
        except (ValueError, OSError) as e:
            messagebox.showerror("Error", f"Failed to scan for orphaned files:\n{e}")
            return

        if not orphaned:
            messagebox.showinfo("Cleanup", "No orphaned properties files found.")
            return

        file_list = "\n".join(f.name for f in orphaned)
        confirmed = messagebox.askyesno(
            "Confirm Cleanup",
            f"The following {len(orphaned)} file(s) are not associated with "
            f"any profile and will be deleted:\n\n{file_list}\n\nProceed?",
        )
        if not confirmed:
            return

        try:
            delete_orphaned_files(orphaned)
        except OSError as e:
            messagebox.showerror("Error", f"Failed to delete orphaned files:\n{e}")
            return

        messagebox.showinfo("Cleanup", f"Deleted {len(orphaned)} orphaned file(s).")
