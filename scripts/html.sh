#!/bin/bash

html_file="your_html_file.html"
text_file="html.txt"

# Check if the HTML file exists, and if not, create it
if [ ! -f "$html_file" ]; then
    echo "<!DOCTYPE html><html><head><title>Your HTML File</title></head><body></body></html>" > "$html_file"
fi

# Open the HTML file
#xdg-open "$html_file" &> /dev/null
# Wait for the HTML file to open

# Write contents of text file into HTML
if [ -f "$text_file" ]; then
    echo "$(cat "$text_file")" > "$html_file"
fi

# Change desktop icon (assuming GNOME desktop environment)
gio set "$html_file" metadata::custom-icon file:///home/b/Desktop/kitty.png