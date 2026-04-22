#!/bin/bash

# Script to generate PyQt5 UI file from .ui file
# Usage: ./run.sh -in <input.ui> [-o <output.py>]

INPUT_FILE=""
OUTPUT_FILE="out.py"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -in)
            INPUT_FILE="$2"
            shift 2
            ;;
        -o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 -in <input.ui> [-o <output.py>]"
            echo ""
            echo "Options:"
            echo "  -in <file>    Input .ui file (required)"
            echo "  -o <file>     Output .py file (default: out.py)"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validate input
if [ -z "$INPUT_FILE" ]; then
    echo "Error: -in parameter is required"
    echo "Usage: $0 -in <input.ui> [-o <output.py>]"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File not found: $INPUT_FILE"
    exit 1
fi

# Check if pyuic5 is available
if ! command -v pyuic5 &> /dev/null; then
    echo "Error: pyuic5 not found. Please install PyQt5:"
    echo "  pip install PyQt5"
    exit 1
fi

# Generate UI file
echo "[1] Generating Python UI from $INPUT_FILE..."
pyuic5 "$INPUT_FILE" -o "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "[2] Success! Generated: $OUTPUT_FILE"
    echo ""
    echo "Next step: Run with rotation wrapper"
    echo "  python rotated_ui.py -in $OUTPUT_FILE"
else
    echo "Error: pyuic5 generation failed"
    exit 1
fi