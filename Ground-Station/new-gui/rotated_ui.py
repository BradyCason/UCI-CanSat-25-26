from PyQt5 import QtCore, QtGui, QtWidgets
import importlib.util
import sys
import os

class RotatedUI:
    """Wrapper that adds rotation to any generated UI"""
    
    def __init__(self, ui_file_path):
        """
        Args:
            ui_file_path: Path to generated UI .py file
        """
        self.ui_file_path = ui_file_path
        self.ui_module = self._load_ui_module(ui_file_path)
        self.Ui_MainWindow = self.ui_module.Ui_MainWindow
    
    def _load_ui_module(self, file_path):
        """Dynamically load UI module from file path"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"UI file not found: {file_path}")
        
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    def _scale_fonts(self, widget, scale_factor):
        """Recursively scale all fonts in a widget tree"""
        font = widget.font()
        font.setPointSize(int(font.pointSize() * scale_factor))
        widget.setFont(font)
        
        # Recursively scale child widgets
        for child in widget.findChildren(QtWidgets.QWidget):
            child_font = child.font()
            child_font.setPointSize(int(child_font.pointSize() * scale_factor))
            child.setFont(child_font)
    
    def setup_rotated_window(self, main_window, rotation_degrees=90, screen_width=1920, screen_height=1080):
        """
        Setup UI with rotation support using a graphics view
        
        Args:
            main_window: QMainWindow instance
            rotation_degrees: Rotation angle (default 90)
            screen_width: Screen width
            screen_height: Screen height
        """
        # Setup UI on main_window
        ui = self.Ui_MainWindow()
        ui.setupUi(main_window)
        
        # Get the actual central widget
        actual_central = main_window.centralWidget()
        
        # Scale all fonts up by 1.5x to compensate for small designer sizes
        self._scale_fonts(actual_central, 1.1)
        
        # Create graphics view and scene
        graphics_view = QtWidgets.QGraphicsView()
        graphics_view.setStyleSheet("border: none; background-color: white;")
        graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        graphics_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        graphics_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        scene = QtWidgets.QGraphicsScene()
        graphics_view.setScene(scene)
        
        # Remove widget from main_window and reparent to None
        main_window.takeCentralWidget()
        actual_central.setParent(None)
        
        # NOW add widget to scene as proxy
        proxy = scene.addWidget(actual_central)
        
        # Set rotation
        proxy.setRotation(rotation_degrees)
        
        # Get bounding rect and set scene bounds
        bounds = scene.itemsBoundingRect()
        scene.setSceneRect(bounds)
        
        # Set graphics view as central widget
        main_window.setCentralWidget(graphics_view)
        
        # Keep content at 1:1 native scale (no fitInView scaling)
        graphics_view.scale(1.0, 1.0)
        
        # Install event filter to catch Escape key
        main_window.keyPressEvent = lambda event: self._handle_key_press(event, main_window)
        
        return ui, proxy
    
    def _handle_key_press(self, event, main_window):
        """Handle key press events; close on Escape"""
        if event.key() == QtCore.Qt.Key_Escape:
            print("[✓] Escape key pressed, closing...")
            main_window.close()
        else:
            # Pass other key events to parent
            QtWidgets.QMainWindow.keyPressEvent(main_window, event)

def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run a generated PyQt5 UI file with rotation support'
    )
    parser.add_argument('-in', '--input', required=True, 
                       help='Input generated UI .py file')
    parser.add_argument('-r', '--rotation', type=int, default=90,
                       help='Rotation angle in degrees (default: 90)')
    parser.add_argument('--width', type=int, default=1920,
                       help='Screen width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080,
                       help='Screen height (default: 1080)')
    
    args = parser.parse_args()
    
    try:
        app = QtWidgets.QApplication(sys.argv)
        main_window = QtWidgets.QMainWindow()
        
        # Load and setup rotated UI
        rotator = RotatedUI(args.input)
        ui, proxy = rotator.setup_rotated_window(main_window, rotation_degrees=args.rotation, 
                                                  screen_width=args.width, screen_height=args.height)
        
        # For 90° rotation: swap width and height so the window fits the rotated content
        if args.rotation == 90 or args.rotation == 270:
            main_window.resize(args.height, args.width)  # swap width/height
        else:
            main_window.resize(args.width, args.height)
        
        # Show fullscreen
        main_window.showFullScreen()
        
        print(f"[✓] Loaded: {args.input}")
        print(f"[✓] Rotation: {args.rotation}°")
        print(f"[✓] Window: {main_window.width()}x{main_window.height()}")
        print(f"[✓] Press ESC to exit")
        
        sys.exit(app.exec_())
    
    except FileNotFoundError as e:
        print(f"[✗] Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[✗] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[✓] Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()