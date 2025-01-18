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

class StoryPlotter:
    def __init__(self, master):
        self.master = master
        master.title("Story Plotter")

        # --- Plot Data ---
        self.main_plot = []  # [(title, description)]
        self.side_plots = {}  # {main_plot_index: {side_plot_index: [(title, description)]}}
        self.side_plot_counts = {}  # {main_plot_index: count}
        self.subplot_colors = {}  # {main_plot_index: color}

        # --- Customization ---
        self.marker_style = 'o'  # Default marker style
        self.available_markers = {  # Define available_markers here
            "Circle": "o",
            "Square": "s",
            "Star": "*",
            "Triangle": "^",
            "Diamond": "D"
        }
        self.background_image_path = None
        self.x_axis_labels = {}


        self.load_presets()  # Load presets on initialization

        # --- GUI and Plot Setup ---
        self.xlabel_entries = []  # List to store x-axis label entry widgets
        self.setup_gui()
        if self.auto_load_preset:  # Check the auto_load flag
            self.load_plot_data(self.load_data_path_preset, startup=True)
            if self.background_image_path_preset:
                self.set_background(self.background_image_path_preset, startup=True)
        self.update_plot()
        self.update_treeview()

    def setup_gui(self):

        # --- Main Frame ---
        self.frame = tk.Frame(self.master, bg="#f0f0f0")
        self.frame.pack(fill="both", expand=True)

        # --- Left Frame (Plot Outline) ---
        self.left_frame = tk.Frame(self.frame, bg="#f0f0f0")
        self.left_frame.pack(side="left", fill="y")

        # --- Title Label for Index ---
        title_label = tk.Label(self.left_frame, text="Content", font=("Arial", 14), bg="#f0f0f0")
        title_label.pack(side="top", fill="x", padx=5, pady=5)

        self.treeview = ttk.Treeview(self.left_frame)
        self.treeview.pack(fill="both", expand=True)
        self.treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)

        # --- Right Frame (Plot and Controls) ---
        self.right_frame = tk.Frame(self.frame, bg="#f0f0f0")
        self.right_frame.pack(side="right", fill="both", expand=True)

        # --- Plot Figure ---
        self.fig, self.ax = plt.subplots(figsize=(12, 8), facecolor="#e6e6e6")  # Larger figure
        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)
        self.ax.spines['left'].set_visible(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect('button_press_event', self.on_plot_click)

        # --- Matplotlib Toolbar ---
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.right_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # --- Button Frame ---
        self.button_frame = tk.Frame(self.right_frame, bg="#f0f0f0")
        self.button_frame.pack(fill="x")

        # --- Button Styling ---
        button_style = ttk.Style()
        button_style.configure("TButton", font=("Arial", 14), padding=8, relief="raised", borderwidth=1,
                               background="#ffffff")  # Larger buttons

        # --- Buttons ---
        self.add_main_button = ttk.Button(
            self.button_frame, text="Add Main Plot Point", style="TButton", command=self.add_main_plot_point
        )
        self.add_main_button.pack(side="left", padx=5, pady=5)

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
        
    def update_xlabels(self):
        # Remove the old x-axis labels
        for text in self.ax.texts:
            if text.get_text() in self.x_axis_labels.values():
                text.remove()

        # Add new x-axis labels
        for i, (title, _) in enumerate(self.main_plot):
            if i in self.x_axis_labels:
                label = self.x_axis_labels[i]
                text = self.ax.text(i, 0.5, label, ha='center', va='bottom', fontsize=12, color='black',
                                    bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'),
                                    transform=self.ax.transData, zorder=10)  # Ensure labels are above other elements
                text.set_clip_on(True)

        self.canvas.draw()

    def set_background(self, image_path=None, startup=False):
        if startup:
            file_path = image_path
        else:
            file_path = filedialog.askopenfilename(
                title="Select Background Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
            )
        if file_path:
            self.background_image_path = file_path
            self.update_plot() # Update the plot first, so background is set before other elements.

            # Set the plot's background to transparent to allow window background
            # to show, after drawing canvas
            self.ax.patch.set_alpha(0.0)
            self.canvas.draw()

            self.master.update()

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
        self.update_plot()

    def save_plot_data(self):
        file_path = simpledialog.askstring("Save Plot", "Enter file path to save:")
        if file_path:
            data = {
                'main_plot': self.main_plot,
                'side_plots': self.side_plots,
                'side_plot_counts': self.side_plot_counts,
                'subplot_colors': self.subplot_colors,
                'marker_style': self.marker_style,
                'background_image_path': self.background_image_path,
                'x_axis_labels': self.x_axis_labels
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f)
                messagebox.showinfo("Save Successful", f"Plot data saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Save Failed", f"Error saving file {e}")
                
    def load_presets(self):
        """Loads presets from presets.json."""
        try:
            with open("presets.json", "r") as f:
                presets = json.load(f)
                self.load_data_path_preset = presets.get("load_data_path")
                self.background_image_path_preset = presets.get("background_image_path")
                self.auto_load_preset = presets.get("auto_load", False)  # Default to False if not specified
        except FileNotFoundError:
            print("Warning: presets.json not found. Using default settings.")
            self.load_data_path_preset = None
            self.background_image_path_preset = None
            self.auto_load_preset = False



    def load_plot_data(self, file_path=None, startup=False):
        if startup:
            load_path = file_path
        else:
            load_path = simpledialog.askstring("Load Plot", "Enter file path to load:")
        if load_path:
            try:
                with open(load_path, 'r') as f:
                    data = json.load(f)
                self.main_plot = data.get('main_plot', [])
                self.side_plots = data.get('side_plots', {})
                self.side_plot_counts = data.get('side_plot_counts', {})
                self.subplot_colors = data.get('subplot_colors', {})
                self.marker_style = data.get('marker_style', 'o')
                self.background_image_path = data.get('background_image_path', None)
                self.x_axis_labels = data.get('x_axis_labels', {})

                # Update marker style dropdown
                for name, style in self.available_markers.items():
                    if style == self.marker_style:
                        self.marker_options.set(name)
                        break

                self.update_plot()
                self.update_treeview()
                messagebox.showinfo("Load Successful", f"Plot data loaded from {load_path}")

            except Exception as e:
                messagebox.showerror("Load Failed", f"Error loading file {e}")
                
    def add_main_plot_point(self):
        editor = self.create_text_editor_window("Add Main Plot Point", "", "")
        editor.wait_window()
        title, description = editor.result
        if title and description:
            self.main_plot.append((title, description))
            
            # Ask for x-axis label when adding a new main plot point
            label = simpledialog.askstring("X-axis Label", "Enter label for this point:")
            if label:
                self.x_axis_labels[len(self.main_plot) - 1] = label
            else:
                self.x_axis_labels[len(self.main_plot) - 1] = f"Main {len(self.main_plot) - 1}"
            
            self.update_plot()
            self.update_treeview()

    def insert_main_plot_point(self, index):
        editor = self.create_text_editor_window("Add Main Plot Point", "", "")
        editor.wait_window()
        title, description = editor.result
        if title and description:
            self.main_plot.insert(index, (title, description))

            # Shift side_plots, side_plot_counts, and subplot_colors
            new_side_plots = {}
            new_side_plot_counts = {}
            new_subplot_colors = {}
            for key, value in self.side_plots.items():
                new_key = key + 1 if key >= index else key
                new_side_plots[new_key] = value
                if key in self.side_plot_counts:
                    new_side_plot_counts[new_key] = self.side_plot_counts[key]
                if key in self.subplot_colors:
                    new_subplot_colors[new_key] = self.subplot_colors[key]

            self.side_plots = new_side_plots
            self.side_plot_counts = new_side_plot_counts
            self.subplot_colors = new_subplot_colors

            # Shift x-axis labels
            new_x_axis_labels = {}
            for key, value in self.x_axis_labels.items():
                new_key = key + 1 if key >= index else key
                new_x_axis_labels[new_key] = value

            # Ask for new x-axis label
            label = simpledialog.askstring("X-axis Label", "Enter label for this point:")
            new_x_axis_labels[index] = label if label else f"Main {index}"
            self.x_axis_labels = new_x_axis_labels

            self.update_plot()
            self.update_treeview()

    def insert_side_plot_point(self, main_index, side_plot_index, index):
        editor = self.create_text_editor_window("Add Side Plot Point", "", "")
        editor.wait_window()
        title, description = editor.result
        if title and description:
            if main_index in self.side_plots and side_plot_index in self.side_plots[main_index]:
                self.side_plots[main_index][side_plot_index].insert(index, (title, description))
                self.update_plot()
                self.update_treeview()
            else:
                messagebox.showerror("Error", "Invalid side plot index.")

    def add_side_plot(self, main_plot_index):
        editor = self.create_text_editor_window("Add Side Plot Point", "", "")
        editor.wait_window()
        title, description = editor.result
        if title and description:
            if main_plot_index not in self.side_plots:
                self.side_plots[main_plot_index] = {}
                self.side_plot_counts[main_plot_index] = 0

            if main_plot_index not in self.subplot_colors:
                self.subplot_colors[main_plot_index] = self._get_random_color()

            self.side_plot_counts[main_plot_index] += 1
            side_plot_index = self.side_plot_counts[main_plot_index]

            if side_plot_index not in self.side_plots[main_plot_index]:
                self.side_plots[main_plot_index][side_plot_index] = []

            self.side_plots[main_plot_index][side_plot_index].append((title, description))
            self.update_plot()
            self.update_treeview()

    def on_plot_click(self, event):
        if event.inaxes == self.ax:
            if event.button is MouseButton.LEFT:
                # Open Plot Point Editor (Main Plot)
                for i, ((title, description), line) in enumerate(zip(self.main_plot, self.main_plot_lines)):
                    contains, _ = line.contains(event)
                    if contains:
                        self.open_plot_point_editor(i, 0, 'main')
                        return

                # Open Plot Point Editor (Side Plot)
                for main_index, side_plot_data in self.side_plots.items():
                    for side_plot_index, points in side_plot_data.items():
                        for i, ((title, description), line) in enumerate(
                                zip(points, self.side_plot_lines[main_index][side_plot_index])):
                            contains, _ = line.contains(event)
                            if contains:
                                self.open_plot_point_editor(main_index, side_plot_index, 'side', side_x_index=i)
                                return

            elif event.button is MouseButton.RIGHT:
                # Context Menu (existing logic - no changes needed here)
                x, y = int(round(event.xdata)), int(round(event.ydata))
                # Check if it's a main plot point
                if y == 0 and 0 <= x < len(self.main_plot):
                    self.show_context_menu(x, 0, 'main')
                else:
                    # Check if it's a side plot point
                    for main_index, side_plot_data in self.side_plots.items():
                        for side_plot_index, points in side_plot_data.items():
                            if x >= main_index and x < main_index + len(
                                    points) and y == -side_plot_index - self.get_offset(main_index, side_plot_index):
                                adjusted_x = x - main_index
                                self.show_context_menu(main_index, side_plot_index, 'side', adjusted_x)
                                return

    def create_text_editor_window(self, title, initial_title, initial_description):
        editor = TextEditorWindow(self.master, title, initial_title, initial_description)
        return editor

    def open_plot_point_editor(self, x_index, y_index, plot_type, side_x_index=None):
        if plot_type == 'main':
            current_title, current_description = self.main_plot[x_index]
            editor = self.create_text_editor_window("Edit Main Plot Point", current_title, current_description)
            editor.wait_window()
            new_title, new_description = editor.result
            if new_title and new_description:
                self.main_plot[x_index] = (new_title, new_description)

                # Prompt for x-axis label update
                if x_index in self.x_axis_labels:
                    new_label = simpledialog.askstring("Update X-axis Label", "Enter new label for this point:",
                                                       initialvalue=self.x_axis_labels[x_index])
                    if new_label:
                        self.x_axis_labels[x_index] = new_label
                    else:
                        # Optionally remove the label if the user cancels or enters nothing
                        del self.x_axis_labels[x_index]

        elif plot_type == 'side':
            current_title, current_description = self.side_plots[x_index][y_index][side_x_index]
            editor = self.create_text_editor_window("Edit Side Plot Point", current_title, current_description)
            editor.wait_window()
            new_title, new_description = editor.result
            if new_title and new_description:
                self.side_plots[x_index][y_index][side_x_index] = (new_title, new_description)
        self.update_plot()
        self.update_treeview()

    def get_offset(self, main_index, side_plot_index):
        offset = 0
        for i in range(main_index):
            if i in self.side_plot_counts:
                offset += self.side_plot_counts[i]
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
                                         lambda: self.open_plot_point_editor(x_index, y_index, plot_type, side_x_index)))
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
        editor = self.create_text_editor_window("Add Side Plot Point", "", "")
        editor.wait_window()
        title, description = editor.result
        if title and description:
            self.side_plots[x_index][y_index].append((title, description))
            self.update_plot()
            self.update_treeview()

    def delete_plot_point(self, x_index, y_index, plot_type, side_x_index=None):
        if plot_type == 'main':
            if messagebox.askyesno("Delete",
                                   "Are you sure you want to delete this main plot point and all associated side plots?"):
                # Delete x-axis label
                if x_index in self.x_axis_labels:
                    del self.x_axis_labels[x_index]

                # Shift subsequent x-axis labels
                new_x_axis_labels = {}
                for key, value in self.x_axis_labels.items():
                    new_key = key if key < x_index else key - 1
                    new_x_axis_labels[new_key] = value
                self.x_axis_labels = new_x_axis_labels
                
                del self.main_plot[x_index]
                if x_index in self.side_plots:
                    del self.side_plots[x_index]
                    del self.side_plot_counts[x_index]
                    del self.subplot_colors[x_index]
                # Rebuild side_plots and side_plot_counts to adjust for removed main plot point
                new_side_plots = {}
                new_side_plot_counts = {}
                new_subplot_colors = {}
                for key, value in self.side_plots.items():
                    new_key = key if key < x_index else key - 1
                    new_side_plots[new_key] = value
                    new_side_plot_counts[new_key] = self.side_plot_counts[key]

                for key, value in self.subplot_colors.items():
                    new_key = key if key < x_index else key - 1
                    new_subplot_colors[new_key] = value

                self.side_plots = new_side_plots
                self.side_plot_counts = new_side_plot_counts
                self.subplot_colors = new_subplot_colors
        elif plot_type == 'side':
            if messagebox.askyesno("Delete", "Are you sure you want to delete this side plot point?"):
                del self.side_plots[x_index][y_index][side_x_index]
                # Check if side plot is now empty and delete it if so
                if not self.side_plots[x_index][y_index]:
                    del self.side_plots[x_index][y_index]
                    self.side_plot_counts[x_index] -= 1
                    # Reorganize side plot indexes if necessary
                    if self.side_plot_counts[x_index] == 0:
                        del self.side_plot_counts[x_index]
                        del self.side_plots[x_index]
                        if x_index in self.subplot_colors:
                            del self.subplot_colors[x_index]
                    else:
                        new_side_plot = {}
                        for key, value in self.side_plots[x_index].items():
                            new_key = key if key < y_index else key - 1
                            new_side_plot[new_key] = value
                        self.side_plots[x_index] = new_side_plot
        self.update_plot()
        self.update_treeview()

    def _get_random_color(self):
        while True:
            color = "#%06x" % random.randint(0, 0xFFFFFF)
            if color not in self.subplot_colors.values():
                return color

    def update_treeview(self):
        # Clear existing items
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        # Add main plot points
        for i, (title, _) in enumerate(self.main_plot):
            main_id = self.treeview.insert("", "end", text=f"Main {i}: {title}")

            # Add side plots for this main plot point
            if i in self.side_plots:
                for side_plot_index, points in self.side_plots[i].items():
                    side_id = self.treeview.insert(main_id, "end", text=f"Side Plot {side_plot_index}")
                    for j, (side_title, _) in enumerate(points):
                        self.treeview.insert(side_id, "end", text=f"Point {j}: {side_title}")

    def on_treeview_select(self, event):
        try:
            selected_id = self.treeview.selection()[0]
            item_text = self.treeview.item(selected_id, "text")

            # Check if it's a main plot point
            if item_text.startswith("Main"):
                main_index = int(item_text.split(":")[0].split(" ")[1])
                # Highlight the point on the plot
                if main_index < len(self.main_plot_lines):
                    line = self.main_plot_lines[main_index]
                    line.set_linewidth(4)  # Make it thicker
                    self.canvas.draw()

            # Check if it's a side plot point
            elif item_text.startswith("Point"):
                parent_id = self.treeview.parent(selected_id)
                grandparent_id = self.treeview.parent(parent_id)
                main_index = int(self.treeview.item(grandparent_id, "text").split(":")[0].split(" ")[1])
                side_plot_index = int(self.treeview.item(parent_id, "text").split(" ")[2])
                side_x_index = int(item_text.split(":")[0].split(" ")[1])
                
                line = self.side_plot_lines[main_index][side_plot_index][side_x_index]
                line.set_linewidth(4)
                self.canvas.draw()

        except IndexError:
            pass  # Ignore if nothing is selected

    def update_plot(self):
        self.ax.clear()

        # --- Adjust Figure and Axes ---
        self.fig.subplots_adjust(left=0.01, right=0.95, top=0.95, bottom=0.01)  # Reduce figure margins

        # --- Set Axis Limits ---
        self.ax.set_xlim(-1, len(self.main_plot) + 1 if self.main_plot else 1)

        # Calculate the maximum y-value needed for side plots
        max_y = 0
        for main_index in range(len(self.main_plot)):
            if main_index in self.side_plot_counts:
                max_y = max(max_y, self.get_offset(main_index, 0) + self.side_plot_counts[main_index])

        self.ax.set_ylim(-max_y - 1, 1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
# --- Draw Main Plot ---
        main_x = range(len(self.main_plot))
        main_y = [0] * len(self.main_plot)
        self.main_plot_lines = []
        if main_x:
            line, = self.ax.plot(main_x, main_y, marker=self.marker_style, linestyle="-", color="#3498db",
                                 markersize=15, linewidth=3, picker=5)
            self.main_plot_lines.append(line)

            # Annotate main plot points
            for i, (title, _) in enumerate(self.main_plot):
                self.ax.annotate(
                    title,
                    (i, 0),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=12,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8)
                )

        # --- Draw Side Plots ---
        self.side_plot_lines = {}
        for main_index, side_plot_data in self.side_plots.items():
            if main_index not in self.side_plot_lines:
                self.side_plot_lines[main_index] = {}
            for side_plot_index, points in side_plot_data.items():
                x_start = main_index
                y = -side_plot_index - self.get_offset(main_index, side_plot_index)
                if side_plot_index not in self.side_plot_lines[main_index]:
                    self.side_plot_lines[main_index][side_plot_index] = []
                # Draw initial vertical line from main plot point
                color = self.subplot_colors.get(main_index, "red")
                line, = self.ax.plot([x_start, x_start], [0, y], linestyle=":", color=color,
                                     markersize=10, linewidth=3, picker=5)
                self.side_plot_lines[main_index][side_plot_index].append(line)

                for i, (title, _) in enumerate(points):
                    x = x_start + i
                    if i == 0:
                        # First point, annotate on the vertical line
                        line, = self.ax.plot(x, y, marker=self.marker_style, linestyle="", color=color,
                                             markersize=10, picker=5)
                        self.side_plot_lines[main_index][side_plot_index].append(line)
                        self.ax.annotate(
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
                        line, = self.ax.plot([x - 1, x], [y, y], marker=self.marker_style, linestyle="-",
                                             color=color, markersize=10, linewidth=3, picker=5)
                        self.side_plot_lines[main_index][side_plot_index].append(line)
                        self.ax.annotate(
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
                self.ax.imshow(img, extent=[self.ax.get_xlim()[0], self.ax.get_xlim()[1],
                                             self.ax.get_ylim()[0], self.ax.get_ylim()[1]], aspect='auto', zorder=-1)
            except Exception as e:
                messagebox.showerror("Error", f"Could not load background image: {e}")

        # Set the facecolor of the plot to transparent after plotting data.
        self.ax.set_facecolor((0, 0, 0, 0))  # Set transparent background.
        self.fig.patch.set_alpha(0.0)  # Ensure figure background is also transparent.
        
        self.update_xlabels()

        self.canvas.draw()

class TextEditorWindow(tk.Toplevel):
    def __init__(self, master, title, initial_title, initial_description):
        super().__init__(master)
        self.title(title)
        self.result = (None, None)  # Store results as title and description
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
        self.result = (title, description)
        self.destroy()

    def on_cancel(self):
        self.result = (None, None)
        self.destroy()

# --- Run the Application ---
if __name__ == "__main__":
    from PIL import Image, ImageTk
    root = tk.Tk()
    plotter = StoryPlotter(root)
    root.mainloop()