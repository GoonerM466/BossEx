import os
import sys
import re
import json # Still needed for config.json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.image import Image # For loading PNG logo
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, DictProperty, ListProperty
from kivy.logger import Logger
from kivy.metrics import dp

# Import your processing modules from the 'bin' directory
# These imports assume 'bin' is added to sys.path by main.py
from name_field import process_name_field
from title_field import process_title_field
from time_field import process_time_field, refresh_time_field
from date_field import process_date_field, refresh_date_field
from auto import auto_process

# Helper: get file path whether .py or PyInstaller .exe or Kivy on Android
# This resource_path is for locating assets relative to the Kivy app's execution.
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'): # PyInstaller
        base_path = sys._MEIPASS
    elif hasattr(sys, '_MEIPASS2'): # Buildozer on Android
        base_path = sys._MEIPASS2
    else: # Development environment
        base_path = os.path.abspath(os.path.dirname(__file__)) # Current script's directory
    
    # For assets like logo.png that might be in the root, go up one level if in 'bin'
    if os.path.basename(base_path) == 'bin':
        base_path = os.path.dirname(base_path)

    return os.path.join(base_path, relative_path)

class BossExApp(App):
    # Kivy Properties for data binding and UI updates
    config = DictProperty({})
    timezone_options = ListProperty([])
    timezone_selection = StringProperty('')
    sample_texts = ListProperty(['' for _ in range(5)])
    sample_check_states = DictProperty({f'sample_{i}': False for i in range(5)})
    regex_expressions = DictProperty({'name': '', 'title': '', 'time': '', 'date': ''})
    regex_check_states = DictProperty({f'regex_{field}': False for field in ['name', 'title', 'time', 'date']})
    format_expressions = DictProperty({'time': '', 'date': ''})
    format_check_states = DictProperty({f'format_{field}': False for field in ['time', 'date']})
    extraction_text = StringProperty('')
    extraction_check_state = BooleanProperty(False)
    test_all_output = StringProperty('')
    test_all_check_state = BooleanProperty(False)
    anchor_enabled = DictProperty({"time": True, "date": True})

    # Internal state for processing
    current_field = StringProperty(None, allownone=True)
    calculated_samples = DictProperty({i: [] for i in range(5)}) # Store highlights
    last_separator = DictProperty({"time": None, "date": None})
    last_pattern = DictProperty({"time": None, "date": None})
    last_time_matches = ListProperty([]) # Store time matches from auto_process

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # The config is now passed directly from main.py
        self.config = kwargs.get('config', {})
        self.max_samples = 5
        self.possible_separators = [item["symbol"] for item in self.config.get("separators", [])]
        self.timezone_options = [tz["friendly_name"] for tz in self.config.get("timezones", [])]
        if self.timezone_options:
            self.timezone_selection = self.timezone_options[0]

    def build(self):
        self.root_widget = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))

        # Logo
        try:
            logo_path = resource_path("logo.png") # Assuming logo.png is in the root
            if os.path.exists(logo_path):
                logo_image = Image(source=logo_path, size_hint_y=None, height=dp(100), allow_stretch=True, keep_ratio=True)
                self.root_widget.add_widget(logo_image)
            else:
                Logger.warning(f"Logo file not found: {logo_path}")
                self.show_message("Warning", "Logo file not found.")
        except Exception as e:
            Logger.error(f"Failed to load logo: {e}")
            self.show_message("Warning", f"Failed to load logo: {e}")

        self.root_widget.add_widget(Label(text="BossEx Alpha V4: AED Regex Builder - A GoonerB Project", size_hint_y=None, height=dp(30)))

        # Timezone dropdown and Auto button
        timezone_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        timezone_layout.add_widget(Label(text="Timezone:", size_hint_x=None, width=dp(80)))
        timezone_spinner = Spinner(
            text=self.timezone_selection,
            values=self.timezone_options,
            size_hint_x=None, width=dp(150)
        )
        timezone_spinner.bind(text=self.setter('timezone_selection'))
        timezone_layout.add_widget(timezone_spinner)
        timezone_layout.add_widget(Button(text="Auto", size_hint_x=None, width=dp(80), on_release=self.auto_process))
        timezone_layout.add_widget(Label()) # Spacer
        self.root_widget.add_widget(timezone_layout)

        # Sample Area
        sample_scroll_view = ScrollView(size_hint_y=None, height=dp(200))
        self.sample_grid = GridLayout(cols=3, size_hint_y=None, spacing=dp(2), padding=dp(5))
        self.sample_grid.bind(minimum_height=self.sample_grid.setter('height'))

        for i in range(self.max_samples):
            checkbox = CheckBox(size_hint_x=None, width=dp(30), active=self.sample_check_states[f'sample_{i}'])
            checkbox.bind(active=lambda instance, value, idx=i: self._set_check_state(f'sample_{idx}', value))
            self.sample_grid.add_widget(checkbox)

            copy_btn = Button(text="Copy", size_hint_x=None, width=dp(60), on_release=lambda instance, idx=i: self.copy_single_field(f"sample_{idx}"))
            self.sample_grid.add_widget(copy_btn)

            text_input = TextInput(text=f"SAMPLE DATA {i+1}", multiline=False, size_hint_y=None, height=dp(30),
                                   on_text_validate=self.update_sample_text)
            text_input.bind(text=lambda instance, value, idx=i: self._update_sample_text_list(idx, value))
            # Store reference to TextInput for later access (e.g., highlighting)
            setattr(self, f'sample_text_input_{i}', text_input)
            self.sample_grid.add_widget(text_input)
        sample_scroll_view.add_widget(self.sample_grid)
        self.root_widget.add_widget(sample_scroll_view)

        # Selection buttons
        button_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        button_layout.add_widget(Button(text="Name", on_release=lambda x: self.select_field("name")))
        button_layout.add_widget(Button(text="Title", on_release=lambda x: self.select_field("title")))
        button_layout.add_widget(Button(text="Time", on_release=lambda x: self.select_field("time")))
        button_layout.add_widget(Button(text="Date", on_release=lambda x: self.select_field("date")))
        button_layout.add_widget(Button(text="Copy All", on_release=self.copy_all))
        button_layout.add_widget(Button(text="Test All", on_release=self.test_all))
        self.root_widget.add_widget(button_layout)

        # Regex and extraction
        self.root_widget.add_widget(Label(text="REGEX EXPRESSIONS", font_size='15sp', bold=True, size_hint_y=None, height=dp(30)))
        regex_grid = GridLayout(cols=7, size_hint_y=None, height=dp(160), spacing=dp(2), padding=dp(5)) # Adjusted height
        regex_fields = ["name", "title", "time", "date"]
        for field in regex_fields:
            checkbox = CheckBox(size_hint_x=None, width=dp(30), active=self.regex_check_states[f'regex_{field}'])
            checkbox.bind(active=lambda instance, value, f=field: self._set_check_state(f'regex_{f}', value))
            regex_grid.add_widget(checkbox)

            copy_btn = Button(text="Copy", size_hint_x=None, width=dp(60), on_release=lambda instance, f=field: self.copy_single_field(f"regex_{f}"))
            regex_grid.add_widget(copy_btn)

            regex_grid.add_widget(Label(text=f"{field.capitalize()}:", size_hint_x=None, width=dp(70)))
            text_input = TextInput(text=self.regex_expressions[field], multiline=False, size_hint_y=None, height=dp(30))
            text_input.bind(text=lambda instance, value, f=field: self.regex_expressions.__setitem__(f, value))
            setattr(self, f'regex_entry_{field}', text_input)
            regex_grid.add_widget(text_input)

            if field in ["time", "date"]:
                refresh_btn = Button(text="Alt.", size_hint_x=None, width=dp(60), on_release=lambda instance, f=field: self.refresh_field(f))
                regex_grid.add_widget(refresh_btn)
                anchor_btn = Button(text="Anchor" if self.anchor_enabled[field] else "No Anchor", size_hint_x=None, width=dp(80), on_release=lambda instance, f=field: self.toggle_anchor(f))
                setattr(self, f'anchor_button_{field}', anchor_btn) # Store reference
                regex_grid.add_widget(anchor_btn)
            else:
                regex_grid.add_widget(Label()) # Placeholder for refresh
                regex_grid.add_widget(Label()) # Placeholder for anchor

            clear_btn = Button(text="Clear", size_hint_x=None, width=dp(60), on_release=lambda instance, f=field: self.clear_field(f))
            regex_grid.add_widget(clear_btn)
        self.root_widget.add_widget(regex_grid)

        # Format boxes
        format_grid = GridLayout(cols=4, size_hint_y=None, height=dp(80), spacing=dp(2), padding=dp(5))
        format_fields = ["time", "date"]
        for field in format_fields:
            checkbox = CheckBox(size_hint_x=None, width=dp(30), active=self.format_check_states[f'format_{field}'])
            checkbox.bind(active=lambda instance, value, f=field: self._set_check_state(f'format_{f}', value))
            format_grid.add_widget(checkbox)

            copy_btn = Button(text="Copy", size_hint_x=None, width=dp(60), on_release=lambda instance, f=field: self.copy_single_field(f"format_{f}"))
            format_grid.add_widget(copy_btn)

            format_grid.add_widget(Label(text=f"{field.capitalize()} Formats:", size_hint_x=None, width=dp(120)))
            text_input = TextInput(text=self.format_expressions[field], multiline=False, size_hint_y=None, height=dp(30))
            text_input.bind(text=lambda instance, value, f=field: self.format_expressions.__setitem__(f, value))
            setattr(self, f'format_entry_{field}', text_input)
            format_grid.add_widget(text_input)
        self.root_widget.add_widget(format_grid)

        # Extraction
        extraction_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        checkbox = CheckBox(size_hint_x=None, width=dp(30), active=self.extraction_check_state)
        checkbox.bind(active=lambda instance, value: self.setter('extraction_check_state')(instance, value))
        extraction_layout.add_widget(checkbox)
        extraction_layout.add_widget(Label(text="Sample Extraction:", size_hint_x=None, width=dp(120)))
        text_input = TextInput(text=self.extraction_text, multiline=False, size_hint_y=None, height=dp(30))
        text_input.bind(text=self.setter('extraction_text'))
        setattr(self, 'extraction_entry', text_input)
        extraction_layout.add_widget(text_input)
        self.root_widget.add_widget(extraction_layout)

        # Test All Extractions
        test_all_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), padding=dp(10), spacing=dp(5))
        test_all_layout.add_widget(Label(text="Test All Extractions", font_size='15sp', bold=True, size_hint_y=None, height=dp(30)))
        checkbox = CheckBox(text="Include in Copy All", size_hint_x=None, width=dp(150), active=self.test_all_check_state)
        checkbox.bind(active=lambda instance, value: self.setter('test_all_check_state')(instance, value))
        test_all_layout.add_widget(checkbox)
        test_all_text_input = TextInput(text=self.test_all_output, readonly=True, multiline=True, size_hint_y=1)
        setattr(self, 'test_all_text', test_all_text_input)
        test_all_layout.add_widget(test_all_text_input)
        self.root_widget.add_widget(test_all_layout)

        # Bind properties to update UI
        self.bind(sample_texts=self.update_sample_text_inputs)
        self.bind(regex_expressions=self.update_regex_entries)
        self.bind(format_expressions=self.update_format_entries)
        self.bind(extraction_text=self.update_extraction_entry)
        self.bind(test_all_output=self.update_test_all_text)

        return self.root_widget

    def _set_check_state(self, key, value):
        if key.startswith('sample_'):
            self.sample_check_states[key] = value
        elif key.startswith('regex_'):
            self.regex_check_states[key] = value
        elif key.startswith('format_'):
            self.format_check_states[key] = value

    def _update_sample_text_list(self, idx, value):
        # Update the internal list property when a TextInput changes
        temp_list = list(self.sample_texts)
        temp_list[idx] = value
        self.sample_texts = temp_list

    def update_sample_text_inputs(self, instance, value):
        # Update TextInput widgets when sample_texts property changes (e.g., after auto_process)
        for i, text_val in enumerate(value):
            text_input_widget = getattr(self, f'sample_text_input_{i}')
            if text_input_widget.text != text_val:
                text_input_widget.text = text_val
            # Clear existing highlights before applying new ones
            text_input_widget.background_color = [1, 1, 1, 1] # White background

        # Re-apply highlights based on calculated_samples
        for sample_idx, highlights in self.calculated_samples.items():
            text_input_widget = getattr(self, f'sample_text_input_{sample_idx}')
            full_text = text_input_widget.text
            # Kivy TextInput doesn't have direct tag_add like Tkinter.
            # For highlighting, we'd typically need to use markup or a custom widget.
            # For now, we'll just set the background color of the whole input if it's highlighted.
            # A more sophisticated solution for specific word highlighting would involve Kivy Text Markup.
            # For simplicity, if any part of a sample is highlighted, we'll change the whole input's background.
            if highlights:
                text_input_widget.background_color = [0.8, 1, 0.8, 1] # Light green for highlighted
            else:
                text_input_widget.background_color = [1, 1, 1, 1] # White

    def update_regex_entries(self, instance, value):
        for field, text_val in value.items():
            text_input_widget = getattr(self, f'regex_entry_{field}')
            if text_input_widget.text != text_val:
                text_input_widget.text = text_val

    def update_format_entries(self, instance, value):
        for field, text_val in value.items():
            text_input_widget = getattr(self, f'format_entry_{field}')
            if text_input_widget.text != text_val:
                text_input_widget.text = text_val

    def update_extraction_entry(self, instance, value):
        self.extraction_entry.text = value

    def update_test_all_text(self, instance, value):
        self.test_all_text.text = value

    def show_message(self, title, message):
        popup = Popup(title=title, content=Label(text=message),
                      size_hint=(0.8, 0.4), auto_dismiss=True)
        popup.open()

    def copy_single_field(self, field_key):
        output = ""
        if field_key.startswith("sample_"):
            idx = int(field_key.split("_")[1])
            content = getattr(self, f'sample_text_input_{idx}').text.strip()
            output = f"Sample {idx+1}: {content}"
        elif field_key.startswith("regex_"):
            field = field_key.split("_")[1]
            content = self.regex_expressions[field].strip()
            output = f"{field.capitalize()} Regex: {content}"
        elif field_key.startswith("format_"):
            field = field_key.split("_")[1]
            content = self.format_expressions[field].strip()
            output = f"{field.capitalize()} Format: {content}"
        elif field_key == "extraction":
            content = self.extraction_text.strip()
            output = f"Extraction: {content}"

        if output:
            from kivy.app import App
            App.get_running_app().clipboard.copy(output)
            self.show_message("Success", f"Copied to clipboard: {output}")
        else:
            self.show_message("Warning", "No content to copy.")

    def copy_all(self, instance):
        output = []
        for i in range(self.max_samples):
            if self.sample_check_states[f"sample_{i}"]:
                content = getattr(self, f'sample_text_input_{i}').text.strip()
                if content:
                    output.append(f"Sample {i+1}: {content}")
        for field in ["name", "title", "time", "date"]:
            if self.regex_check_states[f"regex_{field}"]:
                content = self.regex_expressions[field].strip()
                if content:
                    output.append(f"{field.capitalize()} Regex: {content}")
        for field in ["time", "date"]:
            if self.format_check_states[f"format_{field}"]:
                content = self.format_expressions[field].strip()
                if content:
                    output.append(f"{field.capitalize()} Format: {content}")
        if self.extraction_check_state:
            content = self.extraction_text.strip()
            if content:
                output.append(f"Extraction: {content}")
        if self.test_all_check_state:
            content = self.test_all_output.strip()
            if content:
                output.append("Test All Extractions:\n" + content)

        if output:
            from kivy.app import App
            App.get_running_app().clipboard.copy("\n".join(output))
            self.show_message("Success", "Selected fields copied to clipboard!")
        else:
            self.show_message("Warning", "No fields selected or no content to copy.")

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
        # Update the button text directly
        anchor_btn = getattr(self, f'anchor_button_{field}')
        anchor_btn.text = "Anchor" if self.anchor_enabled[field] else "No Anchor"
        self.select_field(field) # Re-process with new anchor state

    def select_field(self, field):
        self.current_field = field
        selections = []
        new_highlights = {}
        
        # Kivy TextInput doesn't have a direct "sel.first", "sel.last" like Tkinter.
        # We need to rely on the user manually selecting text and then providing it,
        # or implement a custom selection mechanism. For now, we'll assume the user
        # has copied the selected text into the first sample input, or that we're
        # working with the full text of the first sample input.
        # To simulate Tkinter's selection, we'll take the first sample text.
        
        full_text = getattr(self, f'sample_text_input_{0}').text.strip()
        # For simplicity in Kivy, we'll assume the "selection" is just the full text
        # of the first sample input, or you'd need a custom selection mechanism.
        # If you have a specific selection, you'd need to get it from the TextInput's
        # `selection_text` and `selection_from`, `selection_to` properties.
        
        # For now, let's assume the user intends to process the full content of the first sample.
        # If a specific selection is needed, more complex Kivy interaction would be required.
        
        # A more robust approach would be to have a dedicated "Selected Text" input field
        # where the user pastes what they want to process, or to implement custom text selection.
        # For this example, we'll use the full text of the first sample.
        
        selected_text = full_text # Default to full text for processing
        start_idx = 0
        end_idx = len(full_text)

        # If you want to use actual selection from a TextInput:
        # text_input_widget = getattr(self, f'sample_text_input_{0}')
        # if text_input_widget.selection_text:
        #     selected_text = text_input_widget.selection_text
        #     start_idx = text_input_widget.cursor_index() - len(selected_text)
        #     end_idx = text_input_widget.cursor_index()
        #     # Need to find the actual index in the full text, not just cursor relative to selection
        #     # This is more complex and might require iterating through lines or using regex.
        #     # For simplicity, stick to full text or a dedicated input for now.
        
        if not full_text or full_text.startswith("SAMPLE DATA"):
            self.show_message("Warning", "Please enter valid text in Sample 1.")
            return

        timezone = self.timezone_selection
        selected_tz = next((tz for tz in self.config["timezones"] if tz["friendly_name"] == timezone), None)
        tz_matches = selected_tz["match"] if selected_tz else []

        pattern = ""
        part = ""
        format_str = ""
        
        if field == "name":
            pattern, part = process_name_field(
                selected_text, full_text, start_idx, end_idx,
                self.config["name_patterns"], self.possible_separators
            )
            # Kivy doesn't have direct highlight tags like Tkinter.
            # We'll update calculated_samples and rely on update_sample_text_inputs to apply a general highlight.
            if pattern and part:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    start_idx = match.start()
                    end_idx = match.end()
                    self.calculated_samples[0] = [(start_idx, end_idx, field)]
                else:
                    self.calculated_samples[0] = []
            else:
                self.calculated_samples[0] = []
            self.anchor_enabled[field] = False # Name/Title don't use anchor
            
        elif field == "title":
            pattern, part = process_title_field(
                selected_text, full_text, start_idx, end_idx,
                self.possible_separators, self.detect_separator
            )
            if pattern and part:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    start_idx = match.start()
                    end_idx = match.end()
                    self.calculated_samples[0] = [(start_idx, end_idx, field)]
                else:
                    self.calculated_samples[0] = []
            else:
                self.calculated_samples[0] = []
            self.anchor_enabled[field] = False

        elif field == "time":
            pattern, part, format_str = process_time_field(
                selected_text, full_text, start_idx, end_idx,
                self.config["time_formats"], self.possible_separators,
                self.config["days"], self.config["months"],
                self.anchor_enabled["time"], self.detect_separator,
                self.count_separators_before, tz_matches
            )
            if pattern and part:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    start_idx = match.start()
                    end_idx = match.end()
                    self.calculated_samples[0] = [(start_idx, end_idx, field)]
                else:
                    self.calculated_samples[0] = []
            else:
                self.calculated_samples[0] = []
            separator, _ = self.find_previous_separator(full_text, start_idx)
            self.last_separator[field] = separator if separator else "|"
            base_pattern = r"|".join(self.config["time_formats"])
            self.last_pattern[field] = fr"({base_pattern})"

        elif field == "date":
            pattern, part, format_str = process_date_field(
                selected_text, full_text, start_idx, end_idx,
                self.config["date_formats"], self.possible_separators,
                self.config["days"], self.config["months"],
                self.anchor_enabled["date"], self.detect_separator,
                self.count_separators_before, tz_matches
            )
            if pattern and part:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    start_idx = match.start()
                    end_idx = match.end()
                    self.calculated_samples[0] = [(start_idx, end_idx, field)]
                else:
                    self.calculated_samples[0] = []
            else:
                self.calculated_samples[0] = []
            separator, _ = self.find_previous_separator(full_text, start_idx)
            self.last_separator[field] = separator if separator else "|"
            components = identify_components(selected_text, self.config["days"], self.config["months"])
            base_pattern = build_base_pattern(components, self.config["days"], self.config["months"])
            self.last_pattern[field] = fr"({base_pattern})"
        else:
            return

        self.regex_expressions[field] = pattern if pattern else "No pattern detected"
        self.extraction_text = f"[{field}: {part}]"
        if field in ["time", "date"]:
            self.format_expressions[field] = format_str if format_str else "No format detected"
        
        # Trigger UI update for highlights
        self.update_sample_text_inputs(None, self.sample_texts)


    def auto_process(self, instance):
        full_text = getattr(self, f'sample_text_input_{0}').text.strip()
        if not full_text or full_text.startswith("SAMPLE DATA"):
            self.show_message("Warning", "Please enter valid text in Sample 1.")
            return

        timezone = self.timezone_selection
        results = auto_process(full_text, self.config, timezone, self.detect_separator, self.count_separators_before)

        # Store time matches for refresh
        self.last_time_matches = []
        for pattern_str in self.config["time_formats"]:
            for match in re.finditer(pattern_str, full_text, re.IGNORECASE):
                time_text = match.group(0)
                start_idx = match.start()
                is_am_pm = bool(re.search(r'[AaPp][Mm]$', time_text, re.IGNORECASE))
                selected_tz = next((tz for tz in self.config["timezones"] if tz["friendly_name"] == timezone), None)
                tz_score = 0
                if selected_tz:
                    for m in selected_tz["match"]:
                        tz_pos = full_text[max(0, start_idx-20):start_idx].upper().rfind(m)
                        if tz_pos != -1:
                            tz_score = max(tz_score, 20 - tz_pos)
                self.last_time_matches.append((start_idx, start_idx + len(time_text), time_text, pattern_str, is_am_pm, tz_score))
        self.last_time_matches.sort(key=lambda x: (-x[5], not x[4], x[0]))

        # Clear existing fields and update with auto-processed results
        new_regex_expressions = self.regex_expressions.copy()
        new_format_expressions = self.format_expressions.copy()
        new_calculated_samples = {0: []} # Reset highlights for sample 0

        for field in ["name", "title", "time", "date"]:
            new_regex_expressions[field] = results[field]["pattern"] or "No pattern detected"
            if field in ["time", "date"]:
                new_format_expressions[field] = results[field]["format"] or "No format detected"
            self.anchor_enabled[field] = True if field in ["time", "date"] else False
            if field in ["time", "date"]:
                anchor_btn = getattr(self, f'anchor_button_{field}')
                anchor_btn.text = "Anchor"

            if results[field]["pattern"] and results[field]["start_idx"] is not None:
                start_idx = results[field]["start_idx"]
                end_idx = results[field]["end_idx"]
                new_calculated_samples[0].append((start_idx, end_idx, field))

        self.regex_expressions = new_regex_expressions
        self.format_expressions = new_format_expressions
        self.calculated_samples = new_calculated_samples

        # Update extraction
        extraction_parts = [f"{field}: {results[field]['extracted']}" for field in ["name", "title", "time", "date"] if results[field]["extracted"]]
        self.extraction_text = " | ".join(extraction_parts)
        
        # Trigger UI update for highlights
        self.update_sample_text_inputs(None, self.sample_texts)


    def refresh_field(self, field):
        if field not in ["time", "date"]:
            return

        full_text = getattr(self, f'sample_text_input_{0}').text.strip()
        if not full_text or full_text.startswith("SAMPLE DATA"):
            self.show_message("Warning", "Please enter valid text in Sample 1.")
            return

        timezone = self.timezone_selection
        selected_tz = next((tz for tz in self.config["timezones"] if tz["friendly_name"] == timezone), None)
        tz_matches = selected_tz["match"] if selected_tz else []

        current_extracted_value = ""
        # Attempt to parse the current extraction text to get the field's value
        # e.g., "[time: 10:30 AM | date: Jan 1]" -> "10:30 AM"
        extraction_parts = self.extraction_text.split(" | ")
        for part in extraction_parts:
            if part.startswith(f"[{field}:"):
                current_extracted_value = part.replace(f"[{field}:", "").replace("]", "").strip()
                break

        pattern = ""
        extracted = ""
        format_str = ""

        if field == "time":
            pattern, extracted, format_str = refresh_time_field(
                full_text, self.config["time_formats"], self.possible_separators,
                self.config["days"], self.config["months"], self.anchor_enabled["time"],
                self.detect_separator, self.count_separators_before, tz_matches, current_extracted_value
            )
        elif field == "date":
            # For date, refresh_date_field needs selected_text, full_text, start_idx, end_idx
            # Since we don't have a direct selection in Kivy, we'll use the current extracted date
            # as the 'selected_text' for refresh logic, and try to find its position.
            if current_extracted_value:
                start_idx_current = full_text.find(current_extracted_value)
                if start_idx_current != -1:
                    end_idx_current = start_idx_current + len(current_extracted_value)
                    pattern, extracted, format_str = refresh_date_field(
                        current_extracted_value, full_text, start_idx_current, end_idx_current,
                        self.config["date_formats"], self.possible_separators,
                        self.config["days"], self.config["months"],
                        self.anchor_enabled["date"], self.detect_separator,
                        self.count_separators_before
                    )
                else:
                    self.show_message("Warning", f"Could not find '{current_extracted_value}' in sample text for date refresh.")
                    return
            else:
                self.show_message("Warning", "No current date extraction to refresh.")
                return

        new_regex_expressions = self.regex_expressions.copy()
        new_format_expressions = self.format_expressions.copy()
        new_regex_expressions[field] = pattern if pattern else "No pattern detected"
        new_format_expressions[field] = format_str if format_str else "No format detected"
        self.regex_expressions = new_regex_expressions
        self.format_expressions = new_format_expressions

        # Update extraction text (this will override other extractions)
        # A more robust solution would be to update only the specific part of extraction_text
        current_extraction_parts = self.extraction_text.split(" | ")
        updated_extraction_parts = []
        found_field = False
        for part in current_extraction_parts:
            if part.startswith(f"[{field}:"):
                updated_extraction_parts.append(f"[{field}: {extracted}]")
                found_field = True
            else:
                updated_extraction_parts.append(part)
        if not found_field and extracted: # If field wasn't in extraction, add it
            updated_extraction_parts.append(f"[{field}: {extracted}]")
        self.extraction_text = " | ".join(updated_extraction_parts)

        # Update highlights for the refreshed field
        new_calculated_samples_for_0 = [h for h in self.calculated_samples[0] if h[2] != field]
        if extracted:
            start_idx = full_text.find(extracted)
            if start_idx != -1:
                end_idx = start_idx + len(extracted)
                new_calculated_samples_for_0.append((start_idx, end_idx, field))
        self.calculated_samples[0] = new_calculated_samples_for_0
        
        # Trigger UI update for highlights
        self.update_sample_text_inputs(None, self.sample_texts)


    def clear_field(self, field):
        new_regex_expressions = self.regex_expressions.copy()
        new_regex_expressions[field] = ""
        self.regex_expressions = new_regex_expressions

        if field in ["time", "date"]:
            new_format_expressions = self.format_expressions.copy()
            new_format_expressions[field] = ""
            self.format_expressions = new_format_expressions
            self.anchor_enabled[field] = True
            self.last_separator[field] = None
            self.last_pattern[field] = None
            anchor_btn = getattr(self, f'anchor_button_{field}')
            anchor_btn.text = "Anchor"
        
        # Update extraction text (remove this field's extraction)
        current_extraction_parts = self.extraction_text.split(" | ")
        updated_extraction_parts = [
            part for part in current_extraction_parts if not part.startswith(f"[{field}:")
        ]
        self.extraction_text = " | ".join(updated_extraction_parts)

        # Clear highlights for the specific field across all samples
        new_calculated_samples = self.calculated_samples.copy()
        for sample_idx in range(self.max_samples):
            remaining_highlights = [
                (start_idx, end_idx, f) for start_idx, end_idx, f in new_calculated_samples[sample_idx]
                if f != field
            ]
            new_calculated_samples[sample_idx] = remaining_highlights
        self.calculated_samples = new_calculated_samples
        
        # Trigger UI update for highlights
        self.update_sample_text_inputs(None, self.sample_texts)


    def test_all(self, instance):
        summary_lines = []
        for i in range(self.max_samples):
            full_text = getattr(self, f'sample_text_input_{i}').text.strip()
            if full_text and not full_text.startswith("SAMPLE DATA"):
                sample_summary = {"name": "", "title": "", "time": "", "date": ""}

                for field in ["name", "title", "time", "date"]:
                    pattern = self.regex_expressions[field].strip()
                    if pattern and pattern != "No pattern detected":
                        try:
                            match = re.search(pattern, full_text, re.IGNORECASE)
                            if match:
                                # For name, group(0) is fine. For others, group(1) if available, else group(0)
                                extracted = match.group(0).strip()
                                if match.groups(): # If there are capturing groups, use the first one
                                    extracted = match.group(1).strip()
                                
                                if field == "date":
                                    extracted = re.sub(r"(th|rd|st|nd)", "", extracted).strip()
                                sample_summary[field] = extracted
                        except re.error as e:
                            Logger.error(f"Error in {field} regex for sample {i+1}: {e}")

                summary_lines.append(f"SAMPLE {i+1:<12} name: {sample_summary['name']:<30} title: {sample_summary['title']:<40} time: {sample_summary['time']:<15} date: {sample_summary['date']}")

        self.test_all_output = "\n".join(summary_lines)

# Helper functions (from your original gui.py, moved here or imported)
# These functions need to be accessible within the Kivy app class or imported.
# Since they are not part of the BossExApp class, they need to be defined outside it
# or imported from a separate module if they are not already in bin.
# Assuming they are in bin/date_field.py etc. as per your imports.

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

    return r"\s*".join(pattern_parts) # Use \s* for flexible spacing

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
                if int(part) <= 31: # Simple check for date day
                    components.append(("date", part, i, None))
            except ValueError:
                pass
        elif re.match(r"^\d{2,4}$", part):
            components.append(("year", part, i, None))

    return sorted(components, key=lambda x: x[2])