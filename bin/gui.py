import tkinter as tk
from tkinter import messagebox
import re
import base64
import io
import json
import os
import sys
from bin.name_field import process_name_field
from bin.title_field import process_title_field
from bin.time_field import process_time_field, refresh_time_field
from bin.date_field import process_date_field, refresh_date_field
from bin.auto import auto_process

def resource_path(relative_path):
    """Get the absolute path to a resource, works for dev, PyInstaller, and potential Android use."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # When running as a Python script, use the absolute path of the main script's directory
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    return os.path.join(base_path, relative_path)

class BossEx:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.root.title("BossEx Alpha V4: AED Regex Builder - A GoonerB Project")
        self.root.geometry("800x720")
        self.max_samples = 5
        self.current_field = None
        self.calculated_samples = {i: [] for i in range(self.max_samples)}
        self.check_vars = {}
        self.anchor_enabled = {"time": True, "date": True}
        self.last_separator = {"time": None, "date": None}
        self.last_pattern = {"time": None, "date": None}
        self.last_time_matches = []  # Store time matches from auto_process

        # Load config
        self.possible_separators = [item["symbol"] for item in config["separators"]]

        # Load and display the logo from logo.json
        try:
            logo_path = resource_path("logo.json")
            with open(logo_path, "r") as f:
                logo_data = json.load(f)
                logo_b64 = logo_data["logo_b64"]
            logo_bytes = base64.b64decode(logo_b64)
            self.logo_photo = tk.PhotoImage(data=logo_bytes)
            logo_label = tk.Label(self.root, image=self.logo_photo)
            logo_label.pack(pady=10)
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to load logo: {e}")

        # Timezone dropdown and Auto button
        self.timezone_frame = tk.Frame(root)
        self.timezone_frame.pack(pady=5)
        tk.Label(self.timezone_frame, text="Timezone:").pack(side=tk.LEFT, padx=5)
        self.timezone_var = tk.StringVar(value=config["timezones"][0]["friendly_name"])
        timezone_dropdown = tk.OptionMenu(self.timezone_frame, self.timezone_var, *[tz["friendly_name"] for tz in config["timezones"]])
        timezone_dropdown.pack(side=tk.LEFT, padx=5)
        tk.Button(self.timezone_frame, text="Auto", command=self.auto_process).pack(side=tk.LEFT, padx=5)

        # Sample area
        self.sample_frame = tk.Frame(root)
        self.sample_frame.pack(pady=10, fill="x", padx=10)
        self.sample_texts = []
        self.sample_checks = []
        self.sample_copy_buttons = []
        for i in range(self.max_samples):
            var = tk.BooleanVar()
            check = tk.Checkbutton(self.sample_frame, variable=var)
            check.grid(row=i, column=0, padx=5)
            self.check_vars[f"sample_{i}"] = var
            self.sample_checks.append(check)

            copy_btn = tk.Button(self.sample_frame, text="Copy", command=lambda idx=i: self.copy_single_field(f"sample_{idx}"))
            copy_btn.grid(row=i, column=1, padx=2)
            self.sample_copy_buttons.append(copy_btn)

            text = tk.Text(self.sample_frame, height=1, width=50, bg="white")
            text.grid(row=i, column=2, padx=5, pady=2, sticky="ew")
            text.insert("1.0", f"SAMPLE DATA {i+1}")
            text.tag_configure("highlight", background="lightgreen")
            menu = tk.Menu(text, tearoff=0)
            menu.add_command(label="Cut", command=lambda t=text: self.cut_text(t))
            menu.add_command(label="Copy", command=lambda t=text: self.copy_text(t))
            menu.add_command(label="Paste", command=lambda t=text: self.paste_text(t))
            text.bind("<Button-3>", lambda event, m=menu: m.post(event.x_root, event.y_root))
            self.sample_texts.append(text)

        # Selection buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=5)
        tk.Button(self.button_frame, text="Name", command=lambda: self.select_field("name")).grid(row=0, column=0, padx=5)
        tk.Button(self.button_frame, text="Title", command=lambda: self.select_field("title")).grid(row=0, column=1, padx=5)
        tk.Button(self.button_frame, text="Time", command=lambda: self.select_field("time")).grid(row=0, column=2, padx=5)
        tk.Button(self.button_frame, text="Date", command=lambda: self.select_field("date")).grid(row=0, column=3, padx=5)
        tk.Button(self.button_frame, text="Copy All", command=self.copy_all).grid(row=0, column=4, padx=5)
        tk.Button(self.button_frame, text="Test All", command=self.test_all).grid(row=0, column=5, padx=5)

        # Regex and extraction
        self.regex_frame = tk.Frame(root)
        self.regex_frame.pack(pady=5, fill="x", padx=10)
        tk.Label(self.regex_frame, text="REGEX EXPRESSIONS", font=("Arial", 10, "bold")).grid(row=0, column=1, columnspan=6)
        self.regex_labels = {
            "name": tk.Label(self.regex_frame, text="NAME:"),
            "title": tk.Label(self.regex_frame, text="TITLE:"),
            "time": tk.Label(self.regex_frame, text="TIME:"),
            "date": tk.Label(self.regex_frame, text="DATE:")
        }
        self.regex_entries = {
            "name": tk.Entry(self.regex_frame, width=50),
            "title": tk.Entry(self.regex_frame, width=50),
            "time": tk.Entry(self.regex_frame, width=50),
            "date": tk.Entry(self.regex_frame, width=50)
        }
        self.regex_checks = {}
        self.regex_copy_buttons = {}
        for field in ["name", "title", "time", "date"]:
            var = tk.BooleanVar()
            self.regex_checks[field] = tk.Checkbutton(self.regex_frame, variable=var)
            self.check_vars[f"regex_{field}"] = var
            self.regex_copy_buttons[field] = tk.Button(self.regex_frame, text="Copy", command=lambda f=field: self.copy_single_field(f"regex_{f}"))

        self.refresh_buttons = {
            "name": tk.Button(self.regex_frame, text="", state="disabled"),
            "title": tk.Button(self.regex_frame, text="", state="disabled"),
            "time": tk.Button(self.regex_frame, text="Alt.", command=lambda: self.refresh_field("time")),
            "date": tk.Button(self.regex_frame, text="Alt.", command=lambda: self.refresh_field("date"))
        }
        self.anchor_buttons = {
            "time": tk.Button(self.regex_frame, text="Anchor", command=lambda: self.toggle_anchor("time")),
            "date": tk.Button(self.regex_frame, text="Anchor", command=lambda: self.toggle_anchor("date"))
        }
        self.clear_buttons = {
            "name": tk.Button(self.regex_frame, text="Clear", command=lambda: self.clear_field("name")),
            "title": tk.Button(self.regex_frame, text="Clear", command=lambda: self.clear_field("title")),
            "time": tk.Button(self.regex_frame, text="Clear", command=lambda: self.clear_field("time")),
            "date": tk.Button(self.regex_frame, text="Clear", command=lambda: self.clear_field("date"))
        }
        for i, (field, label) in enumerate(self.regex_labels.items()):
            self.regex_checks[field].grid(row=i+1, column=0, padx=5)
            self.regex_copy_buttons[field].grid(row=i+1, column=1, padx=2)
            label.grid(row=i+1, column=2, sticky="w")
            self.regex_entries[field].grid(row=i+1, column=3, pady=2, sticky="ew")
            self.refresh_buttons[field].grid(row=i+1, column=4, padx=5)
            if field in ["time", "date"]:
                self.anchor_buttons[field].grid(row=i+1, column=5, padx=5)
            self.clear_buttons[field].grid(row=i+1, column=6, padx=5)
            menu = tk.Menu(self.regex_entries[field], tearoff=0)
            menu.add_command(label="Cut", command=lambda e=self.regex_entries[field]: self.cut_text(e))
            menu.add_command(label="Copy", command=lambda e=self.regex_entries[field]: self.copy_text(e))
            menu.add_command(label="Paste", command=lambda e=self.regex_entries[field]: self.paste_text(e))
            self.regex_entries[field].bind("<Button-3>", lambda event, m=menu: m.post(event.x_root, event.y_root))

        # Format boxes
        self.format_frame = tk.Frame(root)
        self.format_frame.pack(pady=5, fill="x", padx=10)
        self.format_labels = {
            "time": tk.Label(self.format_frame, text="TIME FORMATS"),
            "date": tk.Label(self.format_frame, text="DATE FORMATS")
        }
        self.format_entries = {
            "time": tk.Entry(self.format_frame, width=50),
            "date": tk.Entry(self.format_frame, width=50)
        }
        self.format_checks = {}
        self.format_copy_buttons = {}
        for field in ["time", "date"]:
            var = tk.BooleanVar()
            self.format_checks[field] = tk.Checkbutton(self.format_frame, variable=var)
            self.check_vars[f"format_{field}"] = var
            self.format_copy_buttons[field] = tk.Button(self.format_frame, text="Copy", command=lambda f=field: self.copy_single_field(f"format_{f}"))

        self.format_checks["time"].grid(row=0, column=0, padx=5)
        self.format_copy_buttons["time"].grid(row=0, column=1, padx=2)
        self.format_labels["time"].grid(row=0, column=2, sticky="w")
        self.format_entries["time"].grid(row=0, column=3, sticky="ew")
        self.format_checks["date"].grid(row=1, column=0, padx=5)
        self.format_copy_buttons["date"].grid(row=1, column=1, padx=2)
        self.format_labels["date"].grid(row=1, column=2, sticky="w")
        self.format_entries["date"].grid(row=1, column=3, sticky="ew")
        for field in ["time", "date"]:
            menu = tk.Menu(self.format_entries[field], tearoff=0)
            menu.add_command(label="Cut", command=lambda e=self.format_entries[field]: self.cut_text(e))
            menu.add_command(label="Copy", command=lambda e=self.format_entries[field]: self.copy_text(e))
            menu.add_command(label="Paste", command=lambda e=self.format_entries[field]: self.paste_text(e))
            self.format_entries[field].bind("<Button-3>", lambda event, m=menu: m.post(event.x_root, event.y_root))

        # Extraction
        self.extraction_frame = tk.Frame(root)
        self.extraction_frame.pack(pady=5, fill="x", padx=10)
        var = tk.BooleanVar()
        self.extraction_check = tk.Checkbutton(self.extraction_frame, variable=var)
        self.check_vars["extraction"] = var
        self.extraction_check.grid(row=0, column=0, padx=5)
        tk.Label(self.extraction_frame, text="sample extraction:").grid(row=0, column=1)
        self.extraction_entry = tk.Entry(self.extraction_frame, width=50)
        self.extraction_entry.grid(row=0, column=2, sticky="ew")
        menu = tk.Menu(self.extraction_entry, tearoff=0)
        menu.add_command(label="Cut", command=lambda e=self.extraction_entry: self.cut_text(e))
        menu.add_command(label="Copy", command=lambda e=self.extraction_entry: self.copy_text(e))
        menu.add_command(label="Paste", command=lambda e=self.extraction_entry: self.paste_text(e))
        self.extraction_entry.bind("<Button-3>", lambda event, m=menu: m.post(event.x_root, event.y_root))

        # Test All
        self.test_all_frame = tk.LabelFrame(root, text="Test All Extractions", padx=10, pady=10)
        self.test_all_frame.pack(pady=5, fill="both", expand=True)
        var = tk.BooleanVar()
        self.test_all_check = tk.Checkbutton(self.test_all_frame, variable=var, text="Include in Copy All")
        self.check_vars["test_all"] = var
        self.test_all_check.grid(row=0, column=0, padx=5, sticky="w")
        self.test_all_text = tk.Text(self.test_all_frame, height=5, width=70, bg="white")
        self.test_all_text.grid(row=1, column=0, columnspan=2, pady=5, sticky="nsew")
        self.test_all_text.config(state="disabled")

        self.sample_frame.grid_columnconfigure(2, weight=1)
        self.regex_frame.grid_columnconfigure(3, weight=1)
        self.format_frame.grid_columnconfigure(3, weight=1)
        self.extraction_frame.grid_columnconfigure(2, weight=1)
        self.test_all_frame.grid_columnconfigure(0, weight=1)
        self.test_all_frame.grid_rowconfigure(1, weight=1)

    def cut_text(self, widget):
        try:
            selected = widget.selection_get()
            widget.delete("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
            self.root.update()
        except tk.TclError:
            pass

    def copy_text(self, widget):
        try:
            selected = widget.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
            self.root.update()
        except tk.TclError:
            pass

    def paste_text(self, widget):
        try:
            clipboard = self.root.clipboard_get()
            widget.insert("insert", clipboard)
        except tk.TclError:
            pass

    def copy_single_field(self, field_key):
        output = ""
        if field_key.startswith("sample_"):
            idx = int(field_key.split("_")[1])
            content = self.sample_texts[idx].get("1.0", "end-1c").strip()
            output = f"Sample {idx+1}: {content}"
        elif field_key.startswith("regex_"):
            field = field_key.split("_")[1]
            content = self.regex_entries[field].get().strip()
            output = f"{field.capitalize()} Regex: {content}"
        elif field_key.startswith("format_"):
            field = field_key.split("_")[1]
            content = self.format_entries[field].get().strip()
            output = f"{field.capitalize()} Format: {content}"
        elif field_key == "extraction":
            content = self.extraction_entry.get().strip()
            output = f"Extraction: {content}"

        if output:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(output)
                self.root.update()
                messagebox.showinfo("Success", f"Copied to clipboard: {output}")
            except tk.TclError as e:
                messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
        else:
            messagebox.showwarning("Warning", "No content to copy.")

    def copy_all(self):
        output = []
        for i in range(self.max_samples):
            if self.check_vars[f"sample_{i}"].get():
                content = self.sample_texts[i].get("1.0", "end-1c").strip()
                if content:
                    output.append(f"Sample {i+1}: {content}")
        for field in ["name", "title", "time", "date"]:
            if self.check_vars[f"regex_{field}"].get():
                content = self.regex_entries[field].get().strip()
                if content:
                    output.append(f"{field.capitalize()} Regex: {content}")
        for field in ["time", "date"]:
            if self.check_vars[f"format_{field}"].get():
                content = self.format_entries[field].get().strip()
                if content:
                    output.append(f"{field.capitalize()} Format: {content}")
        if self.check_vars["extraction"].get():
            content = self.extraction_entry.get().strip()
            if content:
                output.append(f"Extraction: {content}")
        if self.check_vars["test_all"].get():
            content = self.test_all_text.get("1.0", "end-1c").strip()
            if content:
                output.append("Test All Extractions:\n" + content)

        if output:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append("\n".join(output))
                self.root.update()
                messagebox.showinfo("Success", "Selected fields copied to clipboard!")
            except tk.TclError as e:
                messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
        else:
            messagebox.showwarning("Warning", "No fields selected or no content to copy.")

    def find_previous_separator(self, text, end_idx):
        latest_pos = -1
        latest_sep = None
        for sep in self.possible_separators:
            pattern = fr"(?:(?<=[\S])\s*{re.escape(sep)}\s*|^\s*{re.escape(sep)}\s*|\s*{re.escape(sep)}\s*(?=[\S])|\s*{re.escape(sep)}\s*$)"
            matches = [m for m in re.finditer(pattern, text[:end_idx])]
            if matches:
                pos = matches[-1].start()
                if pos > latest_pos:
                    latest_pos = pos
                    latest_sep = sep
        return latest_sep, latest_pos

    def find_next_separator(self, text, start_idx):
        earliest_pos = len(text)
        earliest_sep = None
        for sep in self.possible_separators:
            pattern = fr"(?:(?<=[\S])\s*{re.escape(sep)}\s*|^\s*{re.escape(sep)}\s*|\s*{re.escape(sep)}\s*(?=[\S])|\s*{re.escape(sep)}\s*$)"
            matches = [m for m in re.finditer(pattern, text[start_idx:])]
            if matches:
                pos = matches[0].start() + start_idx
                if pos < earliest_pos:
                    earliest_pos = pos
                    earliest_sep = sep
        return earliest_sep, earliest_pos

    def count_separators_before(self, text, start_idx, separator):
        pattern = fr"(?:(?<=[\S])\s*{re.escape(separator)}\s*|^\s*{re.escape(separator)}\s*|\s*{re.escape(separator)}\s*(?=[\S])|\s*{re.escape(separator)}\s*$)"
        matches = list(re.finditer(pattern, text[:start_idx]))
        return len(matches)

    def detect_separator(self, text):
        max_segments = 1
        selected_separator = None
        for sep in self.possible_separators:
            pattern = fr"(?:(?<=[\S])\s*{re.escape(sep)}\s*|^\s*{re.escape(sep)}\s*|\s*{re.escape(sep)}\s*(?=[\S])|\s*{re.escape(sep)}\s*$)"
            matches = list(re.finditer(pattern, text))
            segments = len(matches) + 1
            if segments > max_segments:
                max_segments = segments
                selected_separator = sep
        return selected_separator if selected_separator else "|"

    def toggle_anchor(self, field):
        if field not in ["time", "date"]:
            return
        self.anchor_enabled[field] = not self.anchor_enabled[field]
        self.anchor_buttons[field].config(text="Anchor" if self.anchor_enabled[field] else "No Anchor")
        self.select_field(field)

    def select_field(self, field):
        self.current_field = field
        selections = []
        new_highlights = {}
        for i, text_widget in enumerate(self.sample_texts):
            full_text = text_widget.get("1.0", "end-1c").strip()
            if full_text and not full_text.startswith("SAMPLE DATA"):
                try:
                    selected_text = text_widget.get("sel.first", "sel.last").strip()
                    if selected_text:
                        start_idx = full_text.index(selected_text)
                        end_idx = start_idx + len(selected_text)
                        selections.append((full_text, selected_text, start_idx, end_idx))
                        if i not in new_highlights:
                            new_highlights[i] = []
                        new_highlights[i].append((start_idx, end_idx, field))
                except (tk.TclError, ValueError):
                    continue

        if not selections:
            messagebox.showwarning("Warning", "Please select text in at least one sample line.")
            return

        full_text, selected_text, start_idx, end_idx = selections[0]
        timezone = self.timezone_var.get()
        selected_tz = next(tz for tz in self.config["timezones"] if tz["friendly_name"] == timezone)
        tz_matches = selected_tz["match"]
        if field == "name":
            pattern, part = process_name_field(
                selected_text, full_text, start_idx, end_idx,
                self.config["name_patterns"], self.possible_separators
            )
            matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
            self.anchor_enabled[field] = False
        elif field == "title":
            pattern, part = process_title_field(
                selected_text, full_text, start_idx, end_idx,
                self.possible_separators, self.detect_separator
            )
            matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
            self.anchor_enabled[field] = False
        elif field == "time":
            pattern, part, format_str = process_time_field(
                selected_text, full_text, start_idx, end_idx,
                self.config["time_formats"], self.possible_separators,
                self.config["days"], self.config["months"],
                self.anchor_enabled["time"], self.detect_separator,
                self.count_separators_before, tz_matches
            )
            base_pattern = r"|".join(self.config["time_formats"])
            matches = list(re.finditer(base_pattern, full_text, re.IGNORECASE))
            separator, _ = self.find_previous_separator(full_text, start_idx)
            self.last_separator[field] = separator if separator else "|"
            self.last_pattern[field] = fr"({base_pattern})"
        elif field == "date":
            pattern, part, format_str = process_date_field(
                selected_text, full_text, start_idx, end_idx,
                self.config["date_formats"], self.possible_separators,
                self.config["days"], self.config["months"],
                self.anchor_enabled["date"], self.detect_separator,
                self.count_separators_before, tz_matches
            )
            components = identify_components(selected_text, self.config["days"], self.config["months"])
            base_pattern = build_base_pattern(components, self.config["days"], self.config["months"])
            matches = list(re.finditer(base_pattern, full_text, re.IGNORECASE))
            separator, _ = self.find_previous_separator(full_text, start_idx)
            self.last_separator[field] = separator if separator else "|"
            self.last_pattern[field] = fr"({base_pattern})"
        else:
            return

        self.regex_entries[field].delete(0, tk.END)
        self.regex_entries[field].insert(0, pattern if pattern else "No pattern detected")
        self.extraction_entry.delete(0, tk.END)
        self.extraction_entry.insert(0, f"[{field}: {part}]")
        if field in ["time", "date"]:
            self.format_entries[field].delete(0, tk.END)
            self.format_entries[field].insert(0, format_str if format_str else "No format detected")

        # Update highlights
        for sample_idx, highlights in new_highlights.items():
            existing_highlights = self.calculated_samples[sample_idx]
            text_widget = self.sample_texts[sample_idx]
            text_widget.tag_remove("highlight", "1.0", "end")
            for start_idx, end_idx, f in existing_highlights:
                if f != field:
                    start_pos = f"1.0 + {start_idx} chars"
                    end_pos = f"1.0 + {end_idx} chars"
                    text_widget.tag_add("highlight", start_pos, end_pos)
            for start_idx, end_idx, f in highlights:
                start_pos = f"1.0 + {start_idx} chars"
                end_pos = f"1.0 + {end_idx} chars"
                text_widget.tag_add("highlight", start_pos, end_pos)
            self.calculated_samples[sample_idx] = [
                h for h in existing_highlights if h[2] != field
            ] + highlights

    def auto_process(self):
        full_text = self.sample_texts[0].get("1.0", "end-1c").strip()
        if not full_text or full_text.startswith("SAMPLE DATA"):
            messagebox.showwarning("Warning", "Please enter valid text in Sample 1.")
            return

        timezone = self.timezone_var.get()
        results = auto_process(full_text, self.config, timezone, self.detect_separator, self.count_separators_before)

        # Store time matches for refresh
        self.last_time_matches = []
        for pattern in self.config["time_formats"]:
            for match in re.finditer(pattern, full_text, re.IGNORECASE):
                time_text = match.group(0)
                start_idx = match.start()
                is_am_pm = bool(re.search(r'[AaPp][Mm]$', time_text, re.IGNORECASE))
                selected_tz = next(tz for tz in self.config["timezones"] if tz["friendly_name"] == timezone)
                tz_score = 0
                for m in selected_tz["match"]:
                    tz_pos = full_text[max(0, start_idx-20):start_idx].upper().rfind(m)
                    if tz_pos != -1:
                        tz_score = max(tz_score, 20 - tz_pos)
                self.last_time_matches.append((start_idx, start_idx + len(time_text), time_text, pattern, is_am_pm, tz_score))
        self.last_time_matches.sort(key=lambda x: (-x[5], not x[4], x[0]))

        # Clear existing fields
        for field in ["name", "title", "time", "date"]:
            self.regex_entries[field].delete(0, tk.END)
            self.regex_entries[field].insert(0, results[field]["pattern"] or "No pattern detected")
            if field in ["time", "date"]:
                self.format_entries[field].delete(0, tk.END)
                self.format_entries[field].insert(0, results[field]["format"] or "No format detected")
            self.anchor_enabled[field] = True if field in ["time", "date"] else False
            if field in ["time", "date"]:
                self.anchor_buttons[field].config(text="Anchor")

        # Update extraction
        self.extraction_entry.delete(0, tk.END)
        extraction_parts = [f"{field}: {results[field]['extracted']}" for field in ["name", "title", "time", "date"] if results[field]["extracted"]]
        self.extraction_entry.insert(0, " | ".join(extraction_parts))

        # Update highlights
        self.sample_texts[0].tag_remove("highlight", "1.0", "end")
        self.calculated_samples[0] = []
        for field in ["name", "title", "time", "date"]:
            if results[field]["pattern"] and results[field]["start_idx"] is not None:
                start_idx = results[field]["start_idx"]
                end_idx = results[field]["end_idx"]
                start_pos = f"1.0 + {start_idx} chars"
                end_pos = f"1.0 + {end_idx} chars"
                self.sample_texts[0].tag_add("highlight", start_pos, end_pos)
                self.calculated_samples[0].append((start_idx, end_idx, field))

    def refresh_field(self, field):
        if field not in ["time", "date"]:
            return

        full_text = self.sample_texts[0].get("1.0", "end-1c").strip()
        if not full_text or full_text.startswith("SAMPLE DATA"):
            messagebox.showwarning("Warning", "Please enter valid text in Sample 1.")
            return

        timezone = self.timezone_var.get()
        selected_tz = next(tz for tz in self.config["timezones"] if tz["friendly_name"] == timezone)
        tz_matches = selected_tz["match"]

        if field == "time" and self.last_time_matches:
            current_time = self.regex_entries["time"].get().strip()
            if current_time.startswith("(?:"):
                current_time = re.search(r"\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?", current_time)
                current_time = current_time.group(0) if current_time else None
            else:
                current_time = None
            pattern, extracted, format_str = refresh_time_field(
                full_text, self.config["time_formats"], self.possible_separators,
                self.config["days"], self.config["months"], self.anchor_enabled["time"],
                self.detect_separator, self.count_separators_before, tz_matches, current_time
            )
            self.regex_entries["time"].delete(0, tk.END)
            self.regex_entries["time"].insert(0, pattern if pattern else "No pattern detected")
            self.extraction_entry.delete(0, tk.END)
            self.extraction_entry.insert(0, f"[time: {extracted}]")
            self.format_entries["time"].delete(0, tk.END)
            self.format_entries["time"].insert(0, format_str if format_str else "No format detected")
            # Update highlights
            start_idx = full_text.find(extracted)
            end_idx = start_idx + len(extracted) if start_idx != -1 else start_idx
            self.sample_texts[0].tag_remove("highlight", "1.0", "end")
            for h in self.calculated_samples[0]:
                if h[2] != "time":
                    start_pos = f"1.0 + {h[0]} chars"
                    end_pos = f"1.0 + {h[1]} chars"
                    self.sample_texts[0].tag_add("highlight", start_pos, end_pos)
            if start_idx != -1:
                start_pos = f"1.0 + {start_idx} chars"
                end_pos = f"1.0 + {end_idx} chars"
                self.sample_texts[0].tag_add("highlight", start_pos, end_pos)
                self.calculated_samples[0] = [h for h in self.calculated_samples[0] if h[2] != "time"] + [(start_idx, end_idx, "time")]
            return

        selections = []
        current_selection = None
        for i, text_widget in enumerate(self.sample_texts):
            full_text = text_widget.get("1.0", "end-1c").strip()
            if full_text and not full_text.startswith("SAMPLE DATA"):
                try:
                    selected_text = text_widget.get("sel.first", "sel.last").strip()
                    if selected_text:
                        start_idx = full_text.index(selected_text)
                        end_idx = start_idx + len(selected_text)
                        selections.append((full_text, selected_text, start_idx, end_idx))
                        if i == 0:
                            current_selection = (full_text, selected_text, start_idx, end_idx)
                except (tk.TclError, ValueError):
                    continue

        if not selections or not current_selection:
            messagebox.showwarning("Warning", "Please select text in at least one sample line.")
            return

        full_text, selected_text, start_idx, end_idx = current_selection
        if field == "time":
            pattern, part, format_str = refresh_time_field(
                full_text, self.config["time_formats"], self.possible_separators,
                self.config["days"], self.config["months"],
                self.anchor_enabled["time"], self.detect_separator,
                self.count_separators_before, tz_matches
            )
        elif field == "date":
            pattern, part, format_str = refresh_date_field(
                selected_text, full_text, start_idx, end_idx,
                self.config["date_formats"], self.possible_separators,
                self.config["days"], self.config["months"],
                self.anchor_enabled["date"], self.detect_separator,
                self.count_separators_before
            )

        self.regex_entries[field].delete(0, tk.END)
        self.regex_entries[field].insert(0, pattern if pattern else "No pattern detected")
        self.extraction_entry.delete(0, tk.END)
        self.extraction_entry.insert(0, f"[{field}: {part}]")
        self.format_entries[field].delete(0, tk.END)
        self.format_entries[field].insert(0, format_str if format_str else "No format detected")

        # Update highlights
        for i, text_widget in enumerate(self.sample_texts):
            text_widget.tag_remove("highlight", "1.0", "end")
            existing_highlights = self.calculated_samples[i]
            for start_idx, end_idx, f in existing_highlights:
                if f != field:
                    start_pos = f"1.0 + {start_idx} chars"
                    end_pos = f"1.0 + {end_idx} chars"
                    text_widget.tag_add("highlight", start_pos, end_pos)
            if i == 0:
                start_pos = f"1.0 + {start_idx} chars"
                end_pos = f"1.0 + {end_idx} chars"
                text_widget.tag_add("highlight", start_pos, end_pos)
                self.calculated_samples[i] = [
                    h for h in existing_highlights if h[2] != field
                ] + [(start_idx, end_idx, field)]

    def clear_field(self, field):
        self.regex_entries[field].delete(0, tk.END)
        self.regex_entries[field].insert(0, "")
        if field in ["time", "date"]:
            self.format_entries[field].delete(0, tk.END)
            self.format_entries[field].insert(0, "")
            self.anchor_enabled[field] = True
            self.last_separator[field] = None
            self.last_pattern[field] = None
            self.anchor_buttons[field].config(text="Anchor")
        self.extraction_entry.delete(0, tk.END)

        for sample_idx in range(self.max_samples):
            text_widget = self.sample_texts[sample_idx]
            text_widget.tag_remove("highlight", "1.0", "end")
            remaining_highlights = [
                (start_idx, end_idx, f) for start_idx, end_idx, f in self.calculated_samples[sample_idx]
                if f != field
            ]
            for start_idx, end_idx, _ in remaining_highlights:
                start_pos = f"1.0 + {start_idx} chars"
                end_pos = f"1.0 + {end_idx} chars"
                text_widget.tag_add("highlight", start_pos, end_pos)
            self.calculated_samples[sample_idx] = remaining_highlights

    def test_all(self):
        summary = []
        for i, text_widget in enumerate(self.sample_texts):
            full_text = text_widget.get("1.0", "end-1c").strip()
            if full_text and not full_text.startswith("SAMPLE DATA"):
                sample_summary = {"name": "", "title": "", "time": "", "date": ""}

                for field in ["name", "title", "time", "date"]:
                    pattern = self.regex_entries[field].get().strip() or "No pattern detected"
                    if pattern != "No pattern detected":
                        try:
                            match = re.search(pattern, full_text, re.IGNORECASE)
                            if match:
                                extracted = match.group(0).strip() if field == "name" else (match.group(1).strip() if match.groups() else match.group(0).strip())
                                if field == "date":
                                    extracted = re.sub(r"(th|rd|st|nd)", "", extracted).strip()
                                sample_summary[field] = extracted
                        except re.error as e:
                            print(f"Error in {field} regex for sample {i+1}: {e}")

                summary.append((f"SAMPLE {i+1}", sample_summary))

        self.test_all_text.config(state="normal")
        self.test_all_text.delete("1.0", "end")
        if summary:
            for sample_name, sample_summary in summary:
                self.test_all_text.insert("end", f"{sample_name:<12} name: {sample_summary['name']:<30} title: {sample_summary['title']:<40} time: {sample_summary['time']:<15} date: {sample_summary['date']}\n")
        self.test_all_text.config(state="disabled")

def build_base_pattern(components, days, months):
    day_short_pattern = "|".join(days["short"])
    day_long_pattern = "|".join(days["long"])
    month_short_pattern = "|".join(months["short"])
    month_long_pattern = "|".join(months["long"])
    date_pattern = r"\d{1,2}"
    year_pattern = r"\d{2,4}"

    pattern_parts = []
    for comp_type, _, _, length in components:
        if comp_type == "day":
            pattern = f"({day_short_pattern})" if length == "short" else f"({day_long_pattern})"
        elif comp_type == "month":
            pattern = f"({month_short_pattern})" if length == "short" else f"({month_long_pattern})"
        elif comp_type == "date":
            pattern = f"({date_pattern})"
        elif comp_type == "year":
            pattern = f"({year_pattern})"
        pattern_parts.append(pattern)

    return r"\s+".join(pattern_parts)

def identify_components(selected_text, days, months):
    cleaned_text = re.sub(r"(th|st|nd|rd)", "", selected_text).strip()
    parts = re.findall(r'\S+', cleaned_text)
    components = []

    for i, part in enumerate(parts):
        part_lower = part.lower()
        if part_lower in [d.lower() for d in days["short"]]:
            components.append(("day", part, i, "short"))
        elif part_lower in [d.lower() for d in days["long"]]:
            components.append(("day", part, i, "long"))
        elif part_lower in [m.lower() for m in months["short"]]:
            components.append(("month", part, i, "short"))
        elif part_lower in [m.lower() for m in months["long"]]:
            components.append(("month", part, i, "long"))
        elif re.match(r"^\d{1,2}$", part):
            try:
                if int(part) <= 31:
                    components.append(("date", part, i, None))
            except ValueError:
                pass
        elif re.match(r"^\d{2,4}$", part):
            components.append(("year", part, i, None))

    return sorted(components, key=lambda x: x[2])