import os
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt

# Dynamic Path Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "data", "camera_data")
MODEL_DIR = os.path.join(REPO_ROOT, "models")
TFLITE_MODEL_PATH = os.path.join(MODEL_DIR, "camera_anomaly.tflite")

# Hyperparameters
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 0.001

def main():
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Data directory {DATA_DIR} does not exist.")
        return
        
    safe_dir = os.path.join(DATA_DIR, "safe")
    threat_dir = os.path.join(DATA_DIR, "threat")
    
    if not os.path.exists(safe_dir) or not os.path.exists(threat_dir):
         print(f"❌ Error: Please ensure both 'safe' and 'threat' directories exist in {DATA_DIR}")
         return
         
    num_safe = len(os.listdir(safe_dir)) if os.path.exists(safe_dir) else 0
    num_threat = len(os.listdir(threat_dir)) if os.path.exists(threat_dir) else 0
    
    if num_safe == 0 or num_threat == 0:
        print(f"⚠️ Warning: Dataset is empty. Found {num_safe} safe images and {num_threat} threat images.")
        print("Please add images to data/camera_data/safe and data/camera_data/threat before training.")
        return

    print("📸 Loading Dataset...")
    train_dataset = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE
    )

    val_dataset = tf.keras.utils.image_dataset_from_directory(
        DATA_DIR,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE
    )

    class_names = train_dataset.class_names
    print(f"🏷️ Classes detected: {class_names}")

    # Prefetch for performance
    AUTOTUNE = tf.data.AUTOTUNE
    train_dataset = train_dataset.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_dataset = val_dataset.cache().prefetch(buffer_size=AUTOTUNE)

    # Data augmentation
    data_augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip('horizontal'),
        tf.keras.layers.RandomRotation(0.2),
    ])

    print("🏗️ Building MobileNetV2 Model...")
    # Preprocessing layer
    preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input

    # Base model
    base_model = MobileNetV2(input_shape=IMG_SIZE + (3,),
                             include_top=False,
                             weights='imagenet')
    
    base_model.trainable = False  # Freeze base model

    # Custom head
    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = data_augmentation(inputs)
    x = preprocess_input(x)
    x = base_model(x, training=False)
    x = GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = Dense(1, activation='sigmoid')(x)

    model = Model(inputs, outputs)

    model.compile(optimizer=Adam(learning_rate=LEARNING_RATE),
                  loss=tf.keras.losses.BinaryCrossentropy(),
                  metrics=['accuracy'])

    model.summary()

    print("🚀 Starting Training...")
    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=EPOCHS
    )

    # Ensure model dir exists
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("💾 Converting to TFLite...")
    # Convert the model
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    # Save the model
    with open(TFLITE_MODEL_PATH, 'wb') as f:
        f.write(tflite_model)
    
    print(f"✅ TFLite model saved to {TFLITE_MODEL_PATH}")

if __name__ == '__main__':
    main()
