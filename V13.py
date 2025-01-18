import matplotlib
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext, filedialog
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.backend_bases import MouseButton
import random
import json
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as mpatches
import matplotlib.image as mpimg
import numpy as np
import matplotlib.image as mpimg
import numpy as np
from PIL import Image, ImageTk
import os

class StoryPlotter:
    def __init__(self, master):
        self.master = master
        master.title("Story Plotter")

        # --- Data Management for Multiple Arcs ---
        self.arcs = {}  # {arc_title: {data}}
        self.current_arc = None  # Currently active arc title

        # --- Customization ---
        self.marker_style = 'o'
        self.available_markers = {
            "Circle": "o",
            "Square": "s",
            "Star": "*",
            "Triangle": "^",
            "Diamond": "D"
        }
        self.background_image_path = None

        self.load_presets()

        # --- GUI and Plot Setup ---
        self.setup_gui()
        if self.auto_load_preset:
            self.load_plot_data(self.load_data_path_preset, startup=True)

    def delete_arc(self, arc_title):
        """Deletes an arc and its associated data and tab."""
        if arc_title in self.arcs:
            # Remove the tab from the notebook
            for i, tab_id in enumerate(self.notebook.tabs()):
                if self.notebook.tab(tab_id, "text") == arc_title:
                    self.notebook.forget(tab_id)
                    break

            # Delete the arc data
            del self.arcs[arc_title]

            # Update current_arc if the deleted arc was the current one
            if self.current_arc == arc_title:
                self.current_arc = None
                if self.notebook.tabs():  # If there are still tabs left
                    new_current_tab_id = self.notebook.select()
                    self.current_arc = self.notebook.tab(new_current_tab_id, "text")
                    self.on_tab_changed(None) # Update visuals
                else:
                    # Handle the case where no tabs are left (optional)
                    # You could create a new empty arc, or just clear the display
                    pass

            # Update treeview
            self.update_treeview()

    def setup_gui(self):
        # --- Main Frame ---
        self.frame = tk.Frame(self.master, bg="#f0f0f0")
        self.frame.pack(fill="both", expand=True)

        # --- Left Frame (Plot Outline) ---
        self.left_frame = tk.Frame(self.frame, bg="#f0f0f0")
        self.left_frame.pack(side="left", fill="y")

        # --- Styling ---
        style = ttk.Style(self.master)

        # Increase tab padding (for overall tab size)
        style.configure("TNotebook", padding=10)  # Add padding around the notebook

        # Increase tab label font size and padding
        style.configure("TNotebook.Tab", padding=[15, 8], font=("Arial", 12))  # Padding: [left, top, right, bottom]

        # --- Title Label for Index ---
        title_label = tk.Label(self.left_frame, text="Content", font=("Arial", 14, "bold"), bg="#f0f0f0")
        title_label.pack(side="top", fill="x", padx=5, pady=5)

        # --- Treeview ---
        self.treeview = ttk.Treeview(self.left_frame, style="Treeview")  # Use a custom style
        style.configure("Treeview", font=("Arial", 12), rowheight=25)  # Increase font size and row height
        self.treeview.pack(fill="both", expand=True)
        self.treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)

        # --- Right Frame (Tabs and Controls) ---
        self.right_frame = tk.Frame(self.frame, bg="#f0f0f0")
        self.right_frame.pack(side="right", fill="both", expand=True)

        # --- Tabbed Interface (Notebook) ---
        self.notebook = ttk.Notebook(self.right_frame, style="TNotebook")  # Use a custom style
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # --- Button Frame ---
        self.button_frame = tk.Frame(self.right_frame, bg="#f0f0f0")
        self.button_frame.pack(fill="x")

        # --- Button Styling ---
        button_style = ttk.Style()
        button_style.configure("TButton", font=("Arial", 14), padding=8, relief="raised", borderwidth=1,
                                background="#ffffff")
        
        # Add a button to delete the current arc
        self.delete_arc_button = ttk.Button(
            self.button_frame, text="Delete Arc", style="TButton", command=lambda: self.delete_arc(self.current_arc)
        )
        self.delete_arc_button.pack(side="left", padx=5, pady=5)

        # --- Buttons ---
        self.add_main_button = ttk.Button(
            self.button_frame, text="Add Main Plot Point", style="TButton", command=self.add_main_plot_point
        )
        self.add_main_button.pack(side="left", padx=5, pady=5)
        
        self.add_arc_button = ttk.Button(
            self.button_frame, text="Add Arc", style="TButton", command=self.add_new_arc
        )
        self.add_arc_button.pack(side="left", padx=5, pady=5)

        self.marker_options = ttk.Combobox(
            self.button_frame,
            values=list(self.available_markers.keys()),
            state="readonly",
            width=10
        )
        self.marker_options.current(0)
        self.marker_options.bind("<<ComboboxSelected>>", self.on_marker_change)
        self.marker_options.pack(side="left", padx=5, pady=5)

        self.bg_button = ttk.Button(
            self.button_frame,
            text="Background", style="TButton",
            command=self.set_background
        )
        self.bg_button.pack(side="left", padx=5, pady=5)

        self.save_button = ttk.Button(
            self.button_frame,
            text="Save", style="TButton",
            command=self.save_plot_data
        )
        self.save_button.pack(side="right", padx=5, pady=5)

        self.load_button = ttk.Button(
            self.button_frame,
            text="Load", style="TButton",
            command=self.load_plot_data
        )
        self.load_button.pack(side="right", padx=5, pady=5)

        self.quit_button = ttk.Button(
            self.button_frame,
            text="Quit", style="TButton",
            command=self.master.destroy
        )
        self.quit_button.pack(side="right", padx=5, pady=5)
# In add_new_arc, when creating a tab, create and store the plot elements
    def add_new_arc(self, arc_title=None, data=None):
        if arc_title is None:
            arc_title = simpledialog.askstring("New Arc", "Enter arc title:", parent=self.master)
        if arc_title:
            if arc_title in self.arcs:
                messagebox.showerror("Error", f"Arc with title '{arc_title}' already exists!")
                return

            # If data is provided, use it; otherwise, create empty data
            if data:
                self.arcs[arc_title] = data
            else:
                self.arcs[arc_title] = {
                    'main_plot': [],
                    'side_plots': {},
                    'side_plot_counts': {},
                    'subplot_colors': {},
                    'marker_style': self.marker_style,
                    'background_image_path': None,
                    'x_axis_labels': {}
                }

            # --- Create a new tab ---
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=arc_title)

            # --- Create plot elements within the tab ---
            fig, ax = plt.subplots(figsize=(8, 6), facecolor="#e6e6e6")
            fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            canvas.mpl_connect('button_press_event',
                               lambda event, a=arc_title: self.on_plot_click(event, a))

            toolbar = NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
            toolbar.update()
            toolbar.pack(side=tk.TOP, fill=tk.X)

            # --- Store references in arc data ---
            self.arcs[arc_title]['fig'] = fig
            self.arcs[arc_title]['ax'] = ax
            self.arcs[arc_title]['canvas'] = canvas
            self.arcs[arc_title]['toolbar'] = toolbar

            self.current_arc = arc_title
            self.notebook.select(len(self.notebook.tabs()) - 1)  # Switch to the new tab
            self.update_plot()
            self.update_treeview()

    def on_tab_changed(self, event):
        # Update current_arc and relevant data when the tab changes
        current_tab_index = self.notebook.index(self.notebook.select())
        self.current_arc = self.notebook.tab(current_tab_index, "text")
        self.marker_style = self.arcs[self.current_arc]['marker_style']
        self.background_image_path = self.arcs[self.current_arc]['background_image_path']

        for name, style in self.available_markers.items():
            if style == self.marker_style:
                self.marker_options.set(name)
                break

        self.update_plot()
        self.update_treeview()

    def get_current_arc_data(self):
        # Helper function to get data for the currently active arc
        if self.current_arc:
            return self.arcs[self.current_arc]
        else:
            return None

    def update_xlabels(self):
        # Make sure to update the plot before calling this function
        arc_data = self.get_current_arc_data()
        if arc_data:
            ax = arc_data['ax']
            x_axis_labels = arc_data['x_axis_labels']
            main_plot = arc_data['main_plot']
            canvas = arc_data['canvas']

            # Remove the old x-axis labels
            for text in ax.texts:
                if text.get_text() in x_axis_labels.values():
                    text.remove()

            # Add new x-axis labels
            for i, (title, _, label) in enumerate(main_plot):
                text = ax.text(i, 0.5, label, ha='center', va='bottom', fontsize=12, color='black',
                                   bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'),
                                   transform=ax.transData, zorder=10)  # Ensure labels are above other elements
                text.set_clip_on(True)

            canvas.draw()

    def set_background(self, image_path=None, startup=False):
        arc_data = self.get_current_arc_data()
        if arc_data:
            if startup:
                file_path = image_path
            else:
                file_path = filedialog.askopenfilename(
                    title="Select Background Image",
                    filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
                )
            if file_path:
                self.background_image_path = file_path
                arc_data['background_image_path'] = file_path
                self.update_plot()

                # Set the plot's background to transparent to allow window background
                # to show, after drawing canvas
                arc_data['ax'].patch.set_alpha(0.0)
                arc_data['canvas'].draw()

                try:
                    self.set_window_background(file_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not set background: {e}")

    def set_window_background(self, image_path):
        try:
            # Open the image using PIL
            pil_image = Image.open(image_path)

            # Resize the image to fit the window
            window_width = self.master.winfo_width()
            window_height = self.master.winfo_height()
            resized_image = pil_image.resize((window_width, window_height), Image.Resampling.LANCZOS)

            # Convert the PIL image to a Tkinter PhotoImage
            self.background_image = ImageTk.PhotoImage(resized_image)

            # Create a label to display the background image
            if not hasattr(self, 'background_label'):
                self.background_label = tk.Label(self.master)
                self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

            self.background_label.configure(image=self.background_image)
            self.background_label.lower()  # Put the label at the bottom of the stacking order

            # Adjust the weights of the grid to ensure the label expands
            self.master.grid_rowconfigure(0, weight=1)
            self.master.grid_columnconfigure(0, weight=1)

        except Exception as e:
            messagebox.showerror("Error", f"Could not set background: {e}")

    def on_marker_change(self, event=None):
        self.marker_style = self.available_markers[self.marker_options.get()]
        arc_data = self.get_current_arc_data()
        if arc_data:
            arc_data['marker_style'] = self.marker_style
            self.update_plot()

    def save_plot_data(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Plot Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            print(f"File path to save: {file_path}")

            # Prepare a serializable dictionary
            serializable_data = {}
            for arc_title, arc_data in self.arcs.items():
                serializable_data[arc_title] = {
                    'main_plot': arc_data['main_plot'],
                    'side_plots': arc_data['side_plots'],
                    'side_plot_counts': arc_data['side_plot_counts'],
                    'subplot_colors': arc_data['subplot_colors'],
                    'marker_style': arc_data['marker_style'],
                    'background_image_path': arc_data['background_image_path'],
                    'x_axis_labels': arc_data['x_axis_labels']
                    # Exclude non-serializable objects like 'fig', 'ax', 'canvas'
                }

            try:
                with open(file_path, 'w') as f:
                    json.dump(serializable_data, f)  # Save the serializable data
                messagebox.showinfo("Save Successful", f"Plot data saved to {file_path}")
            except PermissionError as e:
                messagebox.showerror("Save Failed", f"Permission Error: {e}")
                print(f"Permission Error details: {e}")
            except Exception as e:
                messagebox.showerror("Save Failed", f"Error saving file: {e}")
                print(f"General Exception details: {e}")

    def load_presets(self):
        """Loads presets from presets.json (relative path)."""
        try:
            script_dir = os.path.dirname(__file__)  # Get directory of the script
            presets_file_path = os.path.join(script_dir, "presets.json")  # Construct path relative to script

            with open(presets_file_path, "r") as f:
                presets = json.load(f)

            # Get preset values, handling potential KeyErrors
            self.load_data_path_preset = presets.get("load_data_path")
            self.auto_load_preset = presets.get("auto_load", False)

        except FileNotFoundError:
            print(f"Warning: presets.json not found at {presets_file_path}. Using default settings.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {presets_file_path}. Using default settings.")
        finally:
            # Set default values if not loaded from presets
            self.load_data_path_preset = self.load_data_path_preset or None
            self.auto_load_preset = self.auto_load_preset or False

    def load_plot_data(self, file_path=None, startup=False):
        if startup:
            load_path = file_path
        else:
            load_path = filedialog.askopenfilename(
                title="Load Plot Data",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
        if load_path:
            try:
                with open(load_path, 'r') as f:
                    loaded_data = json.load(f)

                # Create tabs for each arc, along with their data
                for arc_title, data in loaded_data.items():
                    self.add_new_arc(arc_title, data)

                self.update_plot()
                self.update_treeview()
                messagebox.showinfo("Load Successful", f"Plot data loaded from {load_path}")

            except Exception as e:
                messagebox.showerror("Load Failed", f"Error loading file {e}")
                print(f"General Exception details: {e}")

    def add_main_plot_point(self):
        arc_data = self.get_current_arc_data()
        if arc_data:
            editor = self.create_text_editor_window("Add Main Plot Point", "", "",
                                                    f"Label {len(arc_data['main_plot'])}")
            editor.wait_window()
            title, description, label = editor.result
            if title and description:
                if not label:
                    label = f"Label {len(arc_data['main_plot'])}"
                arc_data['main_plot'].append((title, description, label))
                self.update_plot()
                self.update_treeview()

    def insert_main_plot_point(self, index):
        arc_data = self.get_current_arc_data()
        if arc_data:
            editor = self.create_text_editor_window("Add Main Plot Point", "", "", f"Label {index}")
            editor.wait_window()
            title, description, label = editor.result
            if title and description:
                if not label:
                    label = f"Label {index}"
                arc_data['main_plot'].insert(index, (title, description, label))

                # Shift side_plots, side_plot_counts, and subplot_colors
                new_side_plots = {}
                new_side_plot_counts = {}
                new_subplot_colors = {}
                for key, value in arc_data['side_plots'].items():
                    new_key = key + 1 if key >= index else key
                    new_side_plots[new_key] = value
                    if key in arc_data['side_plot_counts']:
                        new_side_plot_counts[new_key] = arc_data['side_plot_counts'][key]
                    if key in arc_data['subplot_colors']:
                        new_subplot_colors[new_key] = arc_data['subplot_colors'][key]

                arc_data['side_plots'] = new_side_plots
                arc_data['side_plot_counts'] = new_side_plot_counts
                arc_data['subplot_colors'] = new_subplot_colors

                self.update_plot()
                self.update_treeview()

    def insert_side_plot_point(self, main_index, side_plot_index, index):
        arc_data = self.get_current_arc_data()
        if arc_data:
            editor = self.create_text_editor_window("Add Side Plot Point", "", "", "")
            editor.wait_window()
            title, description, _ = editor.result  # Ignore label for side plots
            if title and description:
                if main_index in arc_data['side_plots'] and side_plot_index in arc_data['side_plots'][main_index]:
                    arc_data['side_plots'][main_index][side_plot_index].insert(index, (title, description))
                    self.update_plot()
                    self.update_treeview()
                else:
                    messagebox.showerror("Error", "Invalid side plot index.")

    def add_side_plot(self, main_plot_index):
        arc_data = self.get_current_arc_data()
        if arc_data:
            editor = self.create_text_editor_window("Add Side Plot Point", "", "", "")
            editor.wait_window()
            title, description, _ = editor.result  # Ignore label for side plots
            if title and description:
                if main_plot_index not in arc_data['side_plots']:
                    arc_data['side_plots'][main_plot_index] = {}
                    arc_data['side_plot_counts'][main_plot_index] = 0

                if main_plot_index not in arc_data['subplot_colors']:
                    arc_data['subplot_colors'][main_plot_index] = self._get_random_color()

                arc_data['side_plot_counts'][main_plot_index] += 1
                side_plot_index = arc_data['side_plot_counts'][main_plot_index]

                if side_plot_index not in arc_data['side_plots'][main_plot_index]:
                    arc_data['side_plots'][main_plot_index][side_plot_index] = []

                arc_data['side_plots'][main_plot_index][side_plot_index].append((title, description))
                self.update_plot()
                self.update_treeview()

    def on_plot_click(self, event, arc_title):
        if self.current_arc != arc_title:
            return  # Ignore clicks on inactive arcs

        arc_data = self.get_current_arc_data()
        if arc_data:
            ax = arc_data['ax']
            if event.inaxes == ax:
                if event.button is MouseButton.LEFT:
                    # Open Plot Point Editor (Main Plot)
                    for i, ((title, description, label), line) in enumerate(
                            zip(arc_data['main_plot'], arc_data['main_plot_lines'])):
                        contains, _ = line.contains(event)
                        if contains:
                            self.open_plot_point_editor(i, 0, 'main')
                            return

                    # Open Plot Point Editor (Side Plot)
                    for main_index, side_plot_data in arc_data['side_plots'].items():
                        for side_plot_index, points in side_plot_data.items():
                            for i, ((title, description), line) in enumerate(
                                    zip(points, arc_data['side_plot_lines'][main_index][side_plot_index])):
                                contains, _ = line.contains(event)
                                if contains:
                                    self.open_plot_point_editor(main_index, side_plot_index, 'side', side_x_index=i)
                                    return

                elif event.button is MouseButton.RIGHT:
                    x, y = int(round(event.xdata)), int(round(event.ydata))
                    # Check if it's a main plot point
                    if y == 0 and 0 <= x < len(arc_data['main_plot']):
                        self.show_context_menu(x, 0, 'main')
                    else:
                        # Check if it's a side plot point
                        for main_index, side_plot_data in arc_data['side_plots'].items():
                            for side_plot_index, points in side_plot_data.items():
                                if x >= main_index and x < main_index + len(
                                        points) and y == -side_plot_index - self.get_offset(main_index,
                                                                                              side_plot_index):
                                    adjusted_x = x - main_index
                                    self.show_context_menu(main_index, side_plot_index, 'side', adjusted_x)
                                    return

    def create_text_editor_window(self, title, initial_title, initial_description, initial_label):
        editor = TextEditorWindow(self.master, title, initial_title, initial_description, initial_label)
        return editor

    def open_plot_point_editor(self, x_index, y_index, plot_type, side_x_index=None):
        arc_data = self.get_current_arc_data()
        if arc_data:
            if plot_type == 'main':
                current_title, current_description, current_label = arc_data['main_plot'][x_index]
                editor = self.create_text_editor_window("Edit Main Plot Point", current_title, current_description,
                                                        current_label)
                editor.wait_window()
                new_title, new_description, new_label = editor.result
                if new_title is not None and new_description is not None:
                    if not new_label:
                        new_label = f"Label {x_index}"
                    arc_data['main_plot'][x_index] = (new_title, new_description, new_label)

            elif plot_type == 'side':
                current_title, current_description = arc_data['side_plots'][x_index][y_index][side_x_index]
                editor = self.create_text_editor_window("Edit Side Plot Point", current_title, current_description, "")
                editor.wait_window()
                new_title, new_description, _ = editor.result  # Ignore label for side plots
                if new_title is not None and new_description is not None:
                    arc_data['side_plots'][x_index][y_index][side_x_index] = (new_title, new_description)
            self.update_plot()
            self.update_treeview()

    def get_offset(self, main_index, side_plot_index):
        arc_data = self.get_current_arc_data()
        if arc_data:
            offset = 0
            for i in range(main_index):
                if i in arc_data['side_plot_counts']:
                    offset += arc_data['side_plot_counts'][i]
            return offset

    def show_context_menu(self, x_index, y_index, plot_type, side_x_index=None):
        context_menu = tk.Menu(self.master, tearoff=0)
        if plot_type == 'main':
            context_menu.add_command(label="Update",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.open_plot_point_editor(x_index, y_index, plot_type)))
            context_menu.add_command(label="Add Side Plot",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.add_side_plot(x_index)))
            context_menu.add_command(label="Delete",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.delete_plot_point(x_index, y_index, plot_type)))
            context_menu.add_command(label="Add Event Before",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.insert_main_plot_point(x_index)))
            context_menu.add_command(label="Add Event After",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.insert_main_plot_point(x_index + 1)))
        elif plot_type == 'side':
            context_menu.add_command(label="Update",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.open_plot_point_editor(x_index, y_index, plot_type,
                                                                            side_x_index)))
            context_menu.add_command(label="Extend",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.extend_side_plot(x_index, y_index)))
            context_menu.add_command(label="Delete",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.delete_plot_point(x_index, y_index, plot_type, side_x_index)))
            context_menu.add_command(label="Add Event Before",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.insert_side_plot_point(x_index, y_index, side_x_index)))
            context_menu.add_command(label="Add Event After",
                                     command=lambda: self.master.after_idle(
                                         lambda: self.insert_side_plot_point(x_index, y_index, side_x_index + 1)))

        try:
            context_menu.tk_popup(self.master.winfo_pointerx(), self.master.winfo_pointery())
        finally:
            context_menu.grab_release()

    def menu_command_wrapper(self, command, menu):
        """Wrapper to release menu grab after command execution."""
        try:
            command()  # Execute the actual command
        finally:
            menu.grab_release()  # Release the grab in all cases

    def extend_side_plot(self, x_index, y_index):
        arc_data = self.get_current_arc_data()
        if arc_data:
            editor = self.create_text_editor_window("Add Side Plot Point", "", "", "")
            editor.wait_window()
            title, description, _ = editor.result
            if title and description:
                arc_data['side_plots'][x_index][y_index].append((title, description))
                self.update_plot()
                self.update_treeview()

    def delete_plot_point(self, x_index, y_index, plot_type, side_x_index=None):
        arc_data = self.get_current_arc_data()
        if arc_data:
            if plot_type == 'main':
                if messagebox.askyesno("Delete",
                                       "Are you sure you want to delete this main plot point and all associated side plots?"):

                    del arc_data['main_plot'][x_index]
                    if x_index in arc_data['side_plots']:
                        del arc_data['side_plots'][x_index]
                        del arc_data['side_plot_counts'][x_index]
                        del arc_data['subplot_colors'][x_index]
                    # Rebuild side_plots and side_plot_counts to adjust for removed main plot point
                    new_side_plots = {}
                    new_side_plot_counts = {}
                    new_subplot_colors = {}
                    for key, value in arc_data['side_plots'].items():
                        new_key = key if key < x_index else key - 1
                        new_side_plots[new_key] = value
                        new_side_plot_counts[new_key] = arc_data['side_plot_counts'][key]

                    for key, value in arc_data['subplot_colors'].items():
                        new_key = key if key < x_index else key - 1
                        new_subplot_colors[new_key] = value

                    arc_data['side_plots'] = new_side_plots
                    arc_data['side_plot_counts'] = new_side_plot_counts
                    arc_data['subplot_colors'] = new_subplot_colors
            elif plot_type == 'side':
                if messagebox.askyesno("Delete", "Are you sure you want to delete this side plot point?"):
                    del arc_data['side_plots'][x_index][y_index][side_x_index]
                    # Check if side plot is now empty and delete it if so
                    if not arc_data['side_plots'][x_index][y_index]:
                        del arc_data['side_plots'][x_index][y_index]
                        arc_data['side_plot_counts'][x_index] -= 1
                        # Reorganize side plot indexes if necessary
                        if arc_data['side_plot_counts'][x_index] == 0:
                            del arc_data['side_plot_counts'][x_index]
                            del arc_data['side_plots'][x_index]
                            if x_index in arc_data['subplot_colors']:
                                del arc_data['subplot_colors'][x_index]
                        else:
                            new_side_plot = {}
                            for key, value in arc_data['side_plots'][x_index].items():
                                new_key = key if key < y_index else key - 1
                                new_side_plot[new_key] = value
                            arc_data['side_plots'][x_index] = new_side_plot
            self.update_plot()
            self.update_treeview()

    def _get_random_color(self):
        arc_data = self.get_current_arc_data()
        if arc_data:
            while True:
                color = "#%06x" % random.randint(0, 0xFFFFFF)
                if color not in arc_data['subplot_colors'].values():
                    return color

    def update_treeview(self):
        # Clear existing items
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        arc_data = self.get_current_arc_data()
        if arc_data:
            # Add main plot points
            for i, (title, _, _) in enumerate(arc_data['main_plot']):
                main_id = self.treeview.insert("", "end", text=f"Main {i}: {title}")

                # Add side plots for this main plot point
                if i in arc_data['side_plots']:
                    for side_plot_index, points in arc_data['side_plots'][i].items():
                        side_id = self.treeview.insert(main_id, "end", text=f"Side Plot {side_plot_index}")
                        for j, (side_title, _) in enumerate(points):
                            self.treeview.insert(side_id, "end", text=f"Point {j}: {side_title}")

    def on_treeview_select(self, event):
        arc_data = self.get_current_arc_data()
        if not arc_data:
            return

        try:
            selected_id = self.treeview.selection()[0]
            item_text = self.treeview.item(selected_id, "text")

            # Reset linewidth of all lines
            for line in arc_data['main_plot_lines']:
                line.set_linewidth(3)
            for main_index, side_plot_data in arc_data['side_plot_lines'].items():
                for side_plot_index, lines in side_plot_data.items():
                    for line in lines:
                        line.set_linewidth(3)

            # Check if it's a main plot point
            if item_text.startswith("Main"):
                main_index = int(item_text.split(":")[0].split(" ")[1])
                # Highlight the point on the plot
                if main_index < len(arc_data['main_plot_lines']):
                    line = arc_data['main_plot_lines'][main_index]
                    line.set_linewidth(6)  # Make it thicker
                    arc_data['canvas'].draw()

            # Check if it's a side plot point
            elif item_text.startswith("Point"):
                parent_id = self.treeview.parent(selected_id)
                grandparent_id = self.treeview.parent(parent_id)
                main_index = int(self.treeview.item(grandparent_id, "text").split(":")[0].split(" ")[1])
                side_plot_index = int(self.treeview.item(parent_id, "text").split(" ")[2])
                side_x_index = int(item_text.split(":")[0].split(" ")[1])

                line = arc_data['side_plot_lines'][main_index][side_plot_index][side_x_index]
                line.set_linewidth(6)
                arc_data['canvas'].draw()

        except IndexError:
            pass  # Ignore if nothing is selected

    def update_plot(self):
        arc_data = self.get_current_arc_data()
        if not arc_data:
            return

        ax = arc_data['ax']
        canvas = arc_data['canvas']
        main_plot = arc_data['main_plot']
        side_plots = arc_data['side_plots']
        side_plot_counts = arc_data['side_plot_counts']
        subplot_colors = arc_data['subplot_colors']
        marker_style = arc_data['marker_style']

        ax.clear()

        # --- Adjust Figure and Axes ---
        arc_data['fig'].subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)  # Reduce figure margins

        # --- Set Axis Limits ---
        ax.set_xlim(-1, len(main_plot) + 1 if main_plot else 1)

        # Calculate the maximum y-value needed for side plots
        max_y = 0
        for main_index in range(len(main_plot)):
            if main_index in side_plot_counts:
                max_y = max(max_y, self.get_offset(main_index, 0) + side_plot_counts[main_index])

        ax.set_ylim(-max_y - 1, 1)
        ax.set_xticks([])
        ax.set_yticks([])

        # --- Draw Main Plot ---
        main_x = range(len(main_plot))
        main_y = [0] * len(main_plot)
        arc_data['main_plot_lines'] = []
        if main_x:
            line, = ax.plot(main_x, main_y, marker=marker_style, linestyle="-", color="#3498db",
                                 markersize=15, linewidth=3, picker=5)
            arc_data['main_plot_lines'].append(line)

            # Annotate main plot points
            for i, (title, _, _) in enumerate(main_plot):
                ax.annotate(
                    title,
                    (i, 0),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=12,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8)
                )

        # --- Draw Side Plots ---
        arc_data['side_plot_lines'] = {}
        for main_index, side_plot_data in side_plots.items():
            if main_index not in arc_data['side_plot_lines']:
                arc_data['side_plot_lines'][main_index] = {}
            for side_plot_index, points in side_plot_data.items():
                x_start = main_index
                y = -side_plot_index - self.get_offset(main_index, side_plot_index)
                if side_plot_index not in arc_data['side_plot_lines'][main_index]:
                    arc_data['side_plot_lines'][main_index][side_plot_index] = []
                # Draw initial vertical line from main plot point
                color = subplot_colors.get(main_index, "red")
                line, = ax.plot([x_start, x_start], [0, y], linestyle=":", color=color,
                                     markersize=10, linewidth=3, picker=5)
                arc_data['side_plot_lines'][main_index][side_plot_index].append(line)

                for i, (title, _) in enumerate(points):
                    x = x_start + i
                    if i == 0:
                        # First point, annotate on the vertical line
                        line, = ax.plot(x, y, marker=marker_style, linestyle="", color=color,
                                             markersize=10, picker=5)
                        arc_data['side_plot_lines'][main_index][side_plot_index].append(line)
                        ax.annotate(
                            f"SP {side_plot_index}\n{title}",
                            (x, y),
                            textcoords="offset points",
                            xytext=(-20, 0),
                            ha="right",
                            fontsize=10,
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7)
                        )
                    else:
                        # Subsequent points, extend horizontally
                        line, = ax.plot([x - 1, x], [y, y], marker=marker_style, linestyle="-",
                                             color=color, markersize=10, linewidth=3, picker=5)
                        arc_data['side_plot_lines'][main_index][side_plot_index].append(line)
                        ax.annotate(
                            f"{title}",
                            (x, y),
                            textcoords="offset points",
                            xytext=(0, 5),
                            ha="center",
                            fontsize=10,
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7)
                        )

        if self.background_image_path:
            try:
                img = mpimg.imread(self.background_image_path)
                # Ensure the image is displayed behind other plot elements
                ax.imshow(img, extent=[ax.get_xlim()[0], ax.get_xlim()[1],
                                             ax.get_ylim()[0], ax.get_ylim()[1]], aspect='auto', zorder=-1)
            except Exception as e:
                messagebox.showerror("Error", f"Could not load background image: {e}")

        # Set the facecolor of the plot to transparent after plotting data.
        ax.set_facecolor((0, 0, 0, 0))  # Set transparent background.
        arc_data['fig'].patch.set_alpha(0.0)  # Ensure figure background is also transparent.

        self.update_xlabels()

        canvas.draw()

class TextEditorWindow(tk.Toplevel):
    def __init__(self, master, title, initial_title, initial_description, initial_label):
        super().__init__(master)
        self.title(title)
        self.result = (None, None, None)  # Store results as title, description and label
        self.transient(master)  # Keep window on top of the master
        self.grab_set()
        self.config(bg="#f0f0f0")  # Setting the Background color

        # Title Label and Editor
        tk.Label(self, text="Title:", font=("Arial", 14), bg="#f0f0f0").pack(anchor='nw', padx=5, pady=2)
        self.title_text = tk.Text(self, height=1, wrap='none', font=("Arial", 14), bg="#ffffff")
        self.title_text.insert('1.0', initial_title)
        self.title_text.pack(anchor='nw', fill='x', padx=5, pady=2)

        # Description Label and Editor
        tk.Label(self, text="Description:", font=("Arial", 14), bg="#f0f0f0").pack(anchor='nw', padx=5, pady=2)
        self.description_text = scrolledtext.ScrolledText(self, wrap='word', font=("Arial", 14), bg="#ffffff")
        self.description_text.insert('1.0', initial_description)
        self.description_text.pack(anchor='nw', fill='both', expand=True, padx=5, pady=2)

        # Label Label and Editor (Only add if initial_label is provided)
        if initial_label is not None:
            tk.Label(self, text="Label:", font=("Arial", 14), bg="#f0f0f0").pack(anchor='nw', padx=5, pady=2)
            self.label_text = tk.Text(self, height=1, wrap='none', font=("Arial", 14), bg="#ffffff")
            self.label_text.insert('1.0', initial_label)
            self.label_text.pack(anchor='nw', fill='x', padx=5, pady=2)

        # Buttons
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(fill="x")

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side='left', padx=5, pady=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='right', padx=5, pady=5)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.update_idletasks()
        self.geometry(f'+{master.winfo_rootx() + 50}+{master.winfo_rooty() + 50}')
        self.wait_visibility()
        self.lift()

    def on_ok(self):
        title = self.title_text.get("1.0", "end-1c").strip()
        description = self.description_text.get("1.0", "end-1c").strip()
        # Get label only if label_text exists
        label = self.label_text.get("1.0", "end-1c").strip() if hasattr(self, 'label_text') else None
        self.result = (title, description, label)
        self.destroy()

    def on_cancel(self):
        self.result = (None, None, None)
        self.destroy()

# --- Run the Application ---
if __name__ == "__main__":
    root = tk.Tk()
    plotter = StoryPlotter(root)
    root.mainloop()
