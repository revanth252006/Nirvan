import tensorflow as tf
import os

def convert_h5_to_tflite(h5_model_path, tflite_output_path):
    """
    Loads the trained Keras .h5 model and converts it into an optimized
    .tflite model file ready for on-device deployment.
    """
    print(f"--- Loading Keras Model: {h5_model_path} ---")
    if not os.path.exists(h5_model_path):
        print(f"Error: Target model weights not found at {h5_model_path}")
        return

    # 1. Load the existing model
    model = tf.keras.models.load_model(h5_model_path)

    print("--- Converting to TensorFlow Lite Format ---")
    # 2. Initialize the converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # 3. Enable basic structural optimizations
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # 4. Perform the conversion
    tflite_model = converter.convert()

    # 5. Save the flat buffer file to disk
    os.makedirs(os.path.dirname(tflite_output_path), exist_ok=True)
    with open(tflite_output_path, 'wb') as f:
        f.write(tflite_model)
        
    print(f"Successfully generated mobile binary at: {tflite_output_path}")
    print(f"Original Model Size: {os.path.getsize(h5_model_path) / 1024:.2f} KB")
    print(f"Optimized TFLite Size: {os.path.getsize(tflite_output_path) / 1024:.2f} KB")

if __name__ == "__main__":
    h5_path = "models/motion_model.h5"
    tflite_path = "models/motion_model.tflite"
    
    convert_h5_to_tflite(h5_path, tflite_path)