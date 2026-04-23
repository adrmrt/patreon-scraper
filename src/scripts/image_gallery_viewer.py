import os
from tkinter import Frame, Button, Label, Toplevel

from PIL import Image, ImageTk


class ImageGallery:
    SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")

    def __init__(
        self, root, image_dir, rows=5, cols=6, window_width=1000, window_height=900
    ):
        self.root = root
        self.image_dir = image_dir
        self.rows = rows
        self.cols = cols
        self.window_width = window_width
        self.window_height = window_height
        self.images_per_page = rows * cols
        self.current_page = 0

        self.root.title("Image Gallery")
        self.root.resizable(False, False)

        self.image_files = self._get_image_files(image_dir)
        self.loaded_thumbnails = {}  # Cache for thumbnails
        self.open_windows = {}  # Track opened full-size image windows

        self.total_pages = (
            len(self.image_files) + self.images_per_page - 1
        ) // self.images_per_page

        self._setup_ui()

    def _get_image_files(self, directory):
        """Recursively collect all image files from the directory."""
        return [
            os.path.join(root, file)
            for root, _, files in os.walk(directory)
            for file in files
            if file.lower().endswith(self.SUPPORTED_EXTENSIONS)
        ]

    def _setup_ui(self):
        """Set up the main UI components."""
        self._setup_grid_frame()
        self._setup_nav_frame()
        self._update_page()

    def _setup_grid_frame(self):
        """Set up the frame for displaying image thumbnails."""
        self.grid_frame = Frame(
            self.root, width=self.window_width, height=self.window_height
        )
        self.grid_frame.pack_propagate(False)
        self.grid_frame.pack(fill="both", expand=True)

    def _setup_nav_frame(self):
        """Set up the navigation frame with page controls."""
        self.nav_frame = Frame(self.root)
        self.nav_frame.pack()

        # Navigation components
        self.first_page_button = Button(
            self.nav_frame, text="<<", command=self._go_to_first_page
        )
        self.prev_button = Button(
            self.nav_frame, text="<", command=self._go_to_prev_page
        )
        self.page_label = Label(self.nav_frame, text="")
        self.next_button = Button(
            self.nav_frame, text=">", command=self._go_to_next_page
        )
        self.last_page_button = Button(
            self.nav_frame, text=">>", command=self.go_to_last_page
        )

        # Pack components
        self.first_page_button.pack(side="left")
        self.prev_button.pack(side="left")
        self.page_label.pack(side="left")
        self.next_button.pack(side="left")
        self.last_page_button.pack(side="left")

    def _update_page(self):
        """Update the current page's content and navigation controls."""
        self._display_thumbnails()
        self.page_label.config(
            text=f"Page {self.current_page + 1} of {self.total_pages}"
        )

        # Update navigation button states
        self._update_button_state(self.first_page_button, self.current_page == 0)
        self._update_button_state(self.prev_button, self.current_page == 0)
        self._update_button_state(
            self.next_button, self.current_page == self.total_pages - 1
        )
        self._update_button_state(
            self.last_page_button, self.current_page == self.total_pages - 1
        )

    def _update_button_state(self, button, disabled):
        """Enable or disable a button."""
        button.config(state="disabled" if disabled else "normal")

    def _display_thumbnails(self):
        """Clear the grid frame and display the current page's thumbnails."""
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # Calculate the size of each grid square
        grid_width = self.window_width // self.cols
        grid_height = self.window_height // self.rows
        thumb_size = min(grid_width, grid_height) - 10

        start_idx = self.current_page * self.images_per_page
        end_idx = start_idx + self.images_per_page
        images_to_display = self.image_files[start_idx:end_idx]

        for idx, image_path in enumerate(images_to_display):
            thumbnail = self._get_thumbnail(image_path, thumb_size)

            if thumbnail:
                lbl = Label(self.grid_frame, image=thumbnail)
                lbl.image = thumbnail  # Keep a reference to avoid garbage collection
                lbl.grid(
                    row=idx // self.cols,
                    column=idx % self.cols,
                    padx=5,
                    pady=5,
                    sticky="nsew",
                )
                lbl.bind(
                    "<Double-1>", lambda event, p=image_path: self._show_full_image(p)
                )

    def _get_thumbnail(self, image_path, size):
        """Create or retrieve a cached thumbnail for the given image path."""
        if image_path not in self.loaded_thumbnails:
            try:
                image = Image.open(image_path)
                image.thumbnail((size, size))
                self.loaded_thumbnails[image_path] = ImageTk.PhotoImage(image)
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                return None
        return self.loaded_thumbnails[image_path]

    def _show_full_image(self, image_path):
        """Open a new window to display the full-size image."""
        if image_path in self.open_windows:
            self.open_windows[image_path].lift()
            self.open_windows[image_path].focus()
            return

        try:
            image = Image.open(image_path)
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")
            return

        new_window = self._create_image_window(image_path, image)
        self.open_windows[image_path] = new_window

    def _create_image_window(self, image_path, image):
        """Create a new window to display an image."""
        window = Toplevel(self.root)
        window.title(os.path.basename(image_path))
        window.resizable(width=False, height=False)

        # Get the screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        img_width, img_height = image.size

        # Resize the image to fit screen dimensions
        max_width, max_height = int(screen_width * 0.8), int(screen_height * 0.8)

        if img_width > max_width or img_height > max_height:
            scale = min(max_width / img_width, max_height / img_height)
            img_width = int(img_width * scale)
            img_height = int(img_height * scale)
            image = image.resize((img_width, img_height), Image.Resampling.LANCZOS)

        img_display = ImageTk.PhotoImage(image)
        label = Label(window, image=img_display)
        label.image = img_display
        label.pack()

        # Center the window on the screen
        x = (screen_width - img_width) // 2
        y = (screen_height - img_height) // 2
        window.geometry(f"{img_width}x{img_height}+{x}+{y}")

        # Handle window close
        window.protocol(
            "WM_DELETE_WINDOW", lambda: self._on_close_window(image_path, window)
        )
        return window

    def _go_to_first_page(self):
        self.current_page = 0
        self._update_page()

    def _go_to_next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_page()

    def _go_to_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page()

    def go_to_last_page(self):
        self.current_page = self.total_pages - 1
        self._update_page()

    def _on_close_window(self, image_path, window):
        """Handle the closing of an image window."""
        del self.open_windows[image_path]
        window.destroy()
