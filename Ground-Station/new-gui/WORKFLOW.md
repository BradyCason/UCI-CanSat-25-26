# PyQt5 UI Rotation Workflow

## Quick Start

### Step 1: Design UI in Qt Designer
- Open Qt Designer
- Create/edit your `.ui` file (e.g., `my_design.ui`)
- Save the file
- Note: To design a portrait GUI, need to set window geometry in QT Designer to W=1080 x H=1920 (or respective dimensions) 

### Step 2: Generate Python with run.sh
```bash
./run.sh -in my_design.ui -o generated_ui.py
```

**Options:**
- `-in <file>` - Input `.ui` file (required)
- `-o <file>` - Output `.py` file (default: `out.py`)
- `-h` - Show help

### Step 3: Run with Rotation
```bash
python rotated_ui.py -in generated_ui.py
```

**Options:**
- `-in <file>` - Generated UI .py file (required)
- `-r <degrees>` - Rotation angle (default: 90)
- `--width <px>` - Window width (default: 1024)
- `--height <px>` - Window height (default: 768)
- `-h` - Show help

## Full Workflow Example

```bash
# 1. Design in Qt Designer, save as 'ground_station.ui'

# 2. Generate Python file
./run.sh -in ground_station.ui -o gs_ui.py

# 3. Run with 90° rotation, 1920x1080 resolution
python rotated_ui.py -in gs_ui.py -r 90 --width 1920 --height 1080

# 4. Close window and iterate - go back to step 1
```

## One-Liner (if you always use same settings)
```bash
./run.sh -in my_design.ui -o out.py && python rotated_ui.py -in out.py
```

## How It Works

1. **run.sh** - Bash wrapper around `pyuic5`
   - Takes `.ui` file as input
   - Generates clean Python UI code
   - No modifications to generated file

2. **rotated_ui.py** - Rotation wrapper
   - Dynamically imports generated `.py` file
   - Wraps widgets in `QGraphicsView` + `QGraphicsProxyWidget`
   - Applies `QTransform().rotate()` for 90° (or custom angle)
   - Handles all rotation automatically

## Benefits

✅ Clean separation: Qt Designer files stay separate from code  
✅ Reusable: Use same wrapper for any generated UI  
✅ No modifications: Generated files are untouched  
✅ Quick iteration: Edit .ui → run.sh → rotated_ui.py  
✅ Flexible: Customize rotation angle and window size  

## Troubleshooting

### "pyuic5 not found"
```bash
pip install PyQt5
```

### "UI file not found"
Make sure the path to your `.ui` file is correct:
```bash
./run.sh -in ./path/to/my_design.ui -o out.py
```

### Module import errors
Ensure the generated `.py` file has valid Python syntax:
```bash
python -m py_compile generated_ui.py
```

## Next Steps

For more advanced features (custom layouts, event handling), edit your `.py` file after running it through `rotated_ui.py`:

```python
from rotated_ui import RotatedUI
from PyQt5 import QtWidgets

app = QtWidgets.QApplication([])
window = QtWidgets.QMainWindow()

rotator = RotatedUI('generated_ui.py')
ui, proxy = rotator.setup_rotated_window(window, rotation_degrees=90)

# Now you can connect signals, modify UI, etc.
ui.pushButton.clicked.connect(some_function)

window.show()
app.exec_()
```
