import os
import urllib.request as request
from zipfile import ZipFile
import tensorflow as tf
import time
from cnnClassifier.entity.config_entity import TrainingConfig
from pathlib import Path



class Training:
    def __init__(self, config: TrainingConfig):
        self.config = config

    def get_base_model(self):
        self.model = tf.keras.models.load_model(
            self.config.updated_base_model_path
        )

    def train_valid_generator(self):
        datagenerator_kwargs = dict(
            rescale=1.0 / 255,
            validation_split=0.20
        )

        dataflow_kwargs = dict(
            target_size=self.config.params_image_size[:-1],
            batch_size=self.config.params_batch_size,
            interpolation="bicubic"
        )

        valid_datagenerator = tf.keras.preprocessing.image.ImageDataGenerator(
            **datagenerator_kwargs
        )

        self.valid_generator = valid_datagenerator.flow_from_directory(
            directory=self.config.training_data,
            subset="validation",
            shuffle=False,
            **dataflow_kwargs
        )

        if self.config.params_is_augmentation:
            train_datagenerator = tf.keras.preprocessing.image.ImageDataGenerator(
                brightness_range=(0.8, 1.2),
                **datagenerator_kwargs
            )
        else:
            train_datagenerator = valid_datagenerator

        self.train_generator = train_datagenerator.flow_from_directory(
            directory=self.config.training_data,
            subset="training",
            shuffle=True,
            **dataflow_kwargs
        )

    @staticmethod
    def save_model(path: Path, model: tf.keras.Model):
        model.save(path)

    def train(self):
        self.steps_per_epoch = self.train_generator.samples // self.train_generator.batch_size
        self.validation_steps = self.valid_generator.samples // self.valid_generator.batch_size

        # Define the ModelCheckpoint callback
        checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
            filepath=self.config.trained_model_path,  # Save the best model here
            monitor="val_loss",                      # Monitor validation loss
            save_best_only=True,                     # Save only the best model
            mode="min",                              # Minimize the validation loss
            verbose=1                                # Print a message when saving
        )

        # Train the model
        self.model.fit(
            self.train_generator,
            epochs=self.config.params_epochs,
            steps_per_epoch=self.steps_per_epoch,
            validation_steps=self.validation_steps,
            validation_data=self.valid_generator,
            callbacks=[checkpoint_callback]  # Include the callback
        )
