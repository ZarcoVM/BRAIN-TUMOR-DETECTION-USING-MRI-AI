from flask import Flask, render_template, jsonify
import os
import random
from skimage import io, img_as_ubyte
import numpy as np
from flask_cors import CORS
import base64
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'TCGA_HT_8563_19981209')

app = Flask(__name__)
CORS(app)

current_image = None
current_mask = None
current_combined = None
tumor_detected = "Desconocido"
precision_tumor = "N/A"

def convert_to_png(image):
    if image is None:
        return None
    buffer = BytesIO()
    io.imsave(buffer, img_as_ubyte(image), format='png')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

@app.route('/get_image', methods=['GET'])
def get_image():
    image_files = [f for f in os.listdir(IMAGE_DIR) if f.endswith('.tif') and '_mask' not in f]
    if not image_files:
        return jsonify({"error": "No se encontraron imágenes en la carpeta."}), 404
    
    selected_image = random.choice(image_files)
    img_path = os.path.join(IMAGE_DIR, selected_image)
    mask_path = os.path.join(IMAGE_DIR, selected_image.replace('.tif', '_mask.tif'))
    
    try:
        img = io.imread(img_path)
        mask = io.imread(mask_path) if os.path.exists(mask_path) else None
        
        global tumor_detected, precision_tumor, current_image, current_mask, current_combined
        
        if mask is not None and np.any(mask > 0):
            tumor_detected = "Tumor Detectado"
            precision_tumor = f"{np.mean(mask > 0) * 100:.2f}%"
        else:
            tumor_detected = "No hay tumor"
            precision_tumor = "0%"
        
        combined_img = img.copy()
        if mask is not None and mask.shape == img.shape[:2]:
            combined_img[mask > 0] = (255, 0, 0) 
        
        current_image, current_mask, current_combined = img, mask, combined_img
        
        return jsonify({
            "image_base64": convert_to_png(img),
            "mask_base64": convert_to_png(mask),
            "combined_base64": convert_to_png(combined_img),
            "tumor_status": tumor_detected,
            "precision": precision_tumor
        })
    
    except Exception as e:
        return jsonify({"error": f"Error procesando la imagen: {str(e)}"}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
