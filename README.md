# StoryLined-A Visual Storyline Planning & Plotting Tool

## Description

StoryLined is a visual tool designed for writers, game designers, and storytellers to help them plan and visualize their narratives. It allows users to create and manage multiple story arcs, add main and side plot points, customize the appearance of the plot, and save/load their work.

## Features

-   **Multiple Story Arcs:** Manage different story arcs within a single project, each with its own tabbed interface.
-   **Main and Side Plot Points:** Add, edit, and delete main plot points and side plot points to create complex narratives.
-   **Plot Visualization:** Visualize the story flow with a clear and customizable plot diagram.
-   **Customizable Markers:** Choose from various marker styles (Circle, Square, Star, Triangle, Diamond) to represent plot points.
-   **Background Image:** Set a custom background image for the plot area to enhance visualization.
-   **Save and Load:** Save your plot data as a JSON file and load it later to continue working on your story.
-   **Auto-load Preset:** Automatically load a predefined plot data file on startup (configurable in `presets.json`).
-   **Intuitive GUI:** User-friendly interface with a treeview for content overview and a tabbed area for plot visualization.
-   **Context Menu:** Right-click on plot points to access a context menu for quick actions like updating, deleting, and adding side plots.
-   **Plot Point Editor:** A dedicated editor to modify the title, description, and label of plot points.
-   **Drag and Drop:** (Future feature) Drag and drop plot points to rearrange them on the plot.
- **X Labels:** Add descriptive labels on the X-axis for main events.

## Installation

1. **Prerequisites:**
    -   Python 3.x
    -   Required Python libraries: `matplotlib`, `tkinter`, `pillow`

2. **Install Libraries:**
    ```bash
    pip install matplotlib pillow
    ```

3. **Run the Application:**
    ```bash
    python story_plotter.py
    ```
    (Assuming the script is named `story_plotter.py`)

## Usage

(images/Demo.png)

### Basic Navigation

-   **Add Main Plot Point:** Click the "Add Main Plot Point" button to add a new main plot point to the current arc.
-   **Add Arc:** Click the "Add Arc" button to create a new story arc. You'll be prompted to enter a title for the arc.
-   **Switch Arcs:** Click on the tabs at the top to switch between different story arcs.
-   **Delete Arc:** Click the "Delete Arc" button to remove the currently active arc and all its associated data.
-   **Save:** Click the "Save" button to save the current plot data to a JSON file.
-   **Load:** Click the "Load" button to load plot data from a JSON file.
-   **Quit:** Click the "Quit" button to exit the application.
-   **Content Tree:** The left side displays a tree view of the structure, showing main events and their corresponding side events. Clicking on a tree node highlights the corresponding element on the plot.

### Plot Interaction

-   **Click on Plot Point:** Left-click on a plot point (main or side) to open the Plot Point Editor.
-   **Context Menu:** Right-click on a plot point to open a context menu with the following options:
    -   **Update:** Edit the selected plot point's title, description, and label (if applicable).
    -   **Add Side Plot:** (Main plot point only) Add a new side plot branching off the selected main plot point.
    -   **Extend:** (Side plot point only) Add another point to the end of the selected side plot.
    -   **Delete:** Delete the selected plot point.
    -   **Add Event Before/After:** Insert a new main or side event before or after the selected element.

### Customization

-   **Marker Style:** Use the dropdown menu to select the marker style for plot points.
-   **Background Image:** Click the "Background" button to select an image to use as the background for the plot area.
-   **X Labels:** When adding a main event, fill the 'Label' field to add a descriptive label to the X-axis for this event.

### Presets (`presets.json`)

You can configure some default settings in the `presets.json` file:

-   `load_data_path`: The path to a JSON file to be automatically loaded on startup.
-   `auto_load`: Set to `true` to enable auto-loading, `false` to disable.

**Example `presets.json`:**

```json
{
  "load_data_path": "my_story.json",
  "auto_load": true
}
