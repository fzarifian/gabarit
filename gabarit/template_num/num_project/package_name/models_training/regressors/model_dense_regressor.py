#!/usr/bin/env python3

## Dense model for regression
# Copyright (C) <2018-2022>  <Agence Data Services, DSI Pôle Emploi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Classes :
# - ModelDenseRegressor -> Dense model for regression


import os
import json
import shutil
import logging
import dill as pickle
from typing import Union, List, Callable

from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import load_model as load_model_keras
from tensorflow.keras.layers import ELU, BatchNormalization, Dense, Dropout, Input

from {{package_name}}.models_training import utils_deep_keras
from {{package_name}}.models_training.model_keras import ModelKeras
from {{package_name}}.models_training.regressors.model_regressor import ModelRegressorMixin  # type: ignore


class ModelDenseRegressor(ModelRegressorMixin, ModelKeras):
    '''Dense model for regression'''

    _default_name = 'model_dense_regressor'

    def __init__(self, **kwargs) -> None:
        '''Initialization of the class (see ModelClass, ModelKeras & ModelRegressor for more arguments)'''
        # Init.
        super().__init__(**kwargs)

        # Get logger (must be done after super init)
        self.logger = logging.getLogger(__name__)

    def _get_model(self) -> Model:
        '''Gets a model structure

        Returns:
            (Model): A model
        '''
        # Get input/output dimensions
        input_dim = len(self.x_col)

        # Process
        input_layer = Input(shape=(input_dim,))

        x = Dense(64, activation=None, kernel_initializer="he_uniform")(input_layer)
        x = BatchNormalization(momentum=0.9)(x)
        x = ELU(alpha=1.0)(x)
        x = Dropout(0.2)(x)

        x = Dense(64, activation=None, kernel_initializer="he_uniform")(x)
        x = BatchNormalization(momentum=0.9)(x)
        x = ELU(alpha=1.0)(x)
        x = Dropout(0.2)(x)

        # Last layer
        activation = None  # 'relu' if result should be > 0
        out = Dense(1, activation=activation, kernel_initializer='glorot_uniform')(x)

        # Set model
        model = Model(inputs=input_layer, outputs=[out])

        # Set optimizer
        lr = self.keras_params['learning_rate'] if 'learning_rate' in self.keras_params.keys() else 0.001
        decay = self.keras_params['decay'] if 'decay' in self.keras_params.keys() else 0.0
        self.logger.info(f"Learning rate: {lr}")
        self.logger.info(f"Decay: {decay}")
        optimizer = Adam(lr=lr, decay=decay)

        # Set loss & metrics
        loss = 'mean_squared_error'  # could be 'mean_absolute_error'
        metrics: List[Union[str, Callable]] = ['mean_squared_error', 'mean_absolute_error', utils_deep_keras.root_mean_squared_error]

        # Compile model
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        if self.logger.getEffectiveLevel() < logging.ERROR:
            model.summary()

        # Try to save model as png if level_save > 'LOW'
        if self.level_save in ['MEDIUM', 'HIGH']:
            self._save_model_png(model)

        # Return
        return model

    def reload_from_standalone(self, **kwargs) -> None:
        '''Reloads a model from its configuration and "standalones" files
        - /!\\ Experimental /!\\ -

        Kwargs:
            configuration_path (str): Path to configuration file
            hdf5_path (str): Path to hdf5 file
            preprocess_pipeline_path (str): Path to preprocess pipeline
        Raises:
            ValueError: If configuration_path is None
            ValueError: If hdf5_path is None
            ValueError: If preprocess_pipeline_path is None
            FileNotFoundError: If the object configuration_path is not an existing file
            FileNotFoundError: If the object hdf5_path is not an existing file
            FileNotFoundError: If the object preprocess_pipeline_path is not an existing file
        '''
        # Retrieve args
        configuration_path = kwargs.get('configuration_path', None)
        hdf5_path = kwargs.get('hdf5_path', None)
        preprocess_pipeline_path = kwargs.get('preprocess_pipeline_path', None)

        # Checks
        if configuration_path is None:
            raise ValueError("The argument configuration_path can't be None")
        if hdf5_path is None:
            raise ValueError("The argument hdf5_path can't be None")
        if preprocess_pipeline_path is None:
            raise ValueError("The argument preprocess_pipeline_path can't be None")
        if not os.path.exists(configuration_path):
            raise FileNotFoundError(f"The file {configuration_path} does not exist")
        if not os.path.exists(hdf5_path):
            raise FileNotFoundError(f"The file {hdf5_path} does not exist")
        if not os.path.exists(preprocess_pipeline_path):
            raise FileNotFoundError(f"The file {preprocess_pipeline_path} does not exist")

        # Load confs
        with open(configuration_path, 'r', encoding='{{default_encoding}}') as f:
            configs = json.load(f)

        # Set class vars
        # self.model_name = # Keep the created name
        # self.model_dir = # Keep the created folder
        self.nb_fit = configs.get('nb_fit', 1)  # Consider one unique fit by default
        self.trained = configs.get('trained', True)  # Consider trained by default
        # Try to read the following attributes from configs and, if absent, keep the current one
        for attribute in ['model_type', 'x_col', 'y_col', 'columns_in', 'mandatory_columns',
                          'level_save', 'batch_size', 'epochs', 'validation_split', 'patience',
                          'keras_params']:
            setattr(self, attribute, configs.get(attribute, getattr(self, attribute)))

        # Reload model
        self.model = load_model_keras(hdf5_path, custom_objects=self.custom_objects)

        # Save best hdf5 in new folder
        new_hdf5_path = os.path.join(self.model_dir, 'best.hdf5')
        shutil.copyfile(hdf5_path, new_hdf5_path)

        # Reload pipeline preprocessing
        with open(preprocess_pipeline_path, 'rb') as f:
            self.preprocess_pipeline = pickle.load(f)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.error("This script is not stand alone but belongs to a package that has to be imported.")
