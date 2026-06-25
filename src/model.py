import tensorflow as tf
from tensorflow.keras import layers, models

def build_motion_model(window_size=100, num_features=6):
    """
    Builds a lightweight 1D-CNN for mobile sensor data.
    window_size: Number of time steps (e.g., 100 readings = 2 seconds at 50Hz)
    num_features: Number of sensor axes (Accel X,Y,Z + Gyro X,Y,Z = 6)
    """
    model = models.Sequential()

    # Layer 1: The First Net - Looks for immediate, basic patterns like sudden spikes
    model.add(layers.Conv1D(filters=32, kernel_size=3, activation='relu', input_shape=(window_size, num_features)))
    model.add(layers.MaxPooling1D(pool_size=2))

    # Layer 2: The Second Net - Looks for complex sequences (e.g., a fast drop followed by a hard stop)
    model.add(layers.Conv1D(filters=64, kernel_size=3, activation='relu'))
    model.add(layers.MaxPooling1D(pool_size=2))

    # Flatten the timeline into a single row of numbers
    model.add(layers.Flatten())

    # Layer 3: Decision Making
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dropout(0.5)) # Drops 50% of connections randomly to prevent overfitting

    # Output Layer: 1 neuron with Sigmoid activation (Outputs a probability between 0 and 1)
    # 0 = Normal Walk/Run, 1 = Violent Struggle/Fall
    model.add(layers.Dense(1, activation='sigmoid'))

    # Compile the model with standard settings for binary classification
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    return model

# Quick test to see if it builds successfully
if __name__ == "__main__":
    model = build_motion_model()
    model.summary()