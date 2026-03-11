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
    
    def setup_rotated_window(self, main_window, rotation_degrees=90):
        """
        Setup UI with rotation support
        
        Args:
            main_window: QMainWindow instance
            rotation_degrees: Rotation angle (default 90)
        """
        # Create graphics view and scene
        graphics_view = QtWidgets.QGraphicsView()
        graphics_view.setStyleSheet("border: none; background-color: white;")
        graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        
        scene = QtWidgets.QGraphicsScene()
        graphics_view.setScene(scene)
        
        # Setup UI on main_window
        ui = self.Ui_MainWindow()
        ui.setupUi(main_window)
        
        # Get the actual central widget that was set
        actual_central = main_window.centralWidget()
        
        # Temporarily remove the central widget from main_window
        main_window.takeCentralWidget()
        
        # Add it to the graphics scene
        proxy = scene.addWidget(actual_central)
        
        # Apply rotation to the proxy
        transform = QtGui.QTransform().rotate(rotation_degrees)
        proxy.setTransform(transform)
        
        # Adjust scene rect to fit the content
        scene.setSceneRect(scene.itemsBoundingRect())
        
        # Make graphics view expand to fill available space
        graphics_view.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        graphics_view.setMinimumSize(1, 1)
        
        # Set graphics view as the new central widget
        main_window.setCentralWidget(graphics_view)
        
        return ui, proxy

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
                       help='Window width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080,
                       help='Window height (default: 1080)')
    
    args = parser.parse_args()
    
    try:
        app = QtWidgets.QApplication(sys.argv)
        main_window = QtWidgets.QMainWindow()
        
        # Load and setup rotated UI
        rotator = RotatedUI(args.input)
        ui, proxy = rotator.setup_rotated_window(main_window, rotation_degrees=args.rotation)
        
        # Configure window
        main_window.resize(args.width, args.height)
        main_window.show()
        
        print(f"[✓] Loaded: {args.input}")
        print(f"[✓] Rotation: {args.rotation}°")
        print(f"[✓] Window: {args.width}x{args.height}")
        
        sys.exit(app.exec_())
    
    except FileNotFoundError as e:
        print(f"[✗] Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[✗] Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()