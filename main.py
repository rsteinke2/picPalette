from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
from collections import Counter

app = Flask(__name__)

# Configure upload folder and allowed file extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def calculate_color_percentages(image_path, step=32):
    """
    Calculate percentages of grouped colors in an image.

    Args:
        image_path (str): Path to the image.
        step (int): Step size for quantization (e.g., 32, 64).

    Returns:
        list: List of hex color codes and their percentages.
    """
    def quantize_color(color, step):
        return tuple((channel // step) * step for channel in color)

    with Image.open(image_path).convert('RGB') as img:
        # Resize the image for faster processing (optional)
        img = img.resize((100, 100))

        # Convert the image to a NumPy array
        img_array = np.array(img)

        # Reshape to a list of pixels (R, G, B tuples)
        pixels = img_array.reshape((-1, 3))

        # Quantize each pixel color
        quantized_pixels = [quantize_color(pixel, step) for pixel in pixels]

        # Count occurrences of quantized colors
        counter = Counter(quantized_pixels)

        # Total number of pixels
        total_pixels = len(quantized_pixels)

        # Calculate percentage for each quantized color
        color_percentages = {
            color: (count / total_pixels) * 100 for color, count in counter.items()
        }

        # Sort by percentage (descending) and get the top 10 colors
        sorted_colors = sorted(color_percentages.items(), key=lambda x: x[1], reverse=True)[:10]

        # Convert quantized RGB to Hex
        hex_colors = [
            (f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}", percentage)
            for color, percentage in sorted_colors
        ]

        return hex_colors


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if the POST request has a file
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]

        # If no file is selected
        if file.filename == "":
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Secure the filename and save it
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            # Calculate color percentages
            colors = calculate_color_percentages(file_path)

            return render_template("index.html", image_url=file_path, colors=colors)

    # Render the form if GET request
    return render_template("index.html", image_url=None)


if __name__ == "__main__":
    app.run(debug=True)
