#!/usr/bin/env python3

## Classes to explain models predictions
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
# - Explainer -> Parent class for the explainers
# - LimeExplainer -> Lime Explainer wrapper class

import logging
import numpy as np
from typing import Type, Union, Any
from lime.explanation import Explanation
from lime.lime_text import LimeTextExplainer

from {{package_name}}.preprocessing import preprocess
from {{package_name}}.models_training.model_class import ModelClass


class Explainer:
    '''Parent class for the explainers'''

    def __init__(self) -> None:
        '''Initialization of the parent class'''
        self.logger = logging.getLogger(__name__)

    def explain_instance(self, content: str, **kwargs) -> Any:
        '''Explains a prediction

        Args:
            content (str): Text to be explained
        Returns:
            (?): An explanation object
        '''
        raise NotImplementedError("'explain_instance' needs to be overridden")

    def explain_instance_as_html(self, content: str, **kwargs) -> str:
        '''Explains a prediction - returns an HTML object

        Args:
            content (str): Text to be explained
        Returns:
            str: An HTML code with the explanation
        '''
        raise NotImplementedError("'explain_instance_as_html' needs to be overridden")

    def explain_instance_as_list(self, content: str, **kwargs) -> list:
        '''Explains a prediction - returns a list object

        Args:
            content (str): Text to be explained
        Returns:
            list: List of tuples with words and corresponding weights
        '''
        raise NotImplementedError("'explain_instance_as_list' needs to be overridden")


class LimeExplainer(Explainer):
    '''Lime Explainer wrapper class'''

    def __init__(self, model: Type[ModelClass], model_conf: dict) -> None:
        ''' Initialization

        Args:
            model: A model instance with predict & predict_proba functions, and list_classes attribute
            model_conf (dict): The model's configuration
        Raises:
            TypeError: If the provided model does not implement a `predict_proba` function
            TypeError: If the provided model does not have a `list_classes` attribute
        '''
        super().__init__()
        pred_proba_op = getattr(model, "predict_proba", None)

        if pred_proba_op is None or not callable(pred_proba_op):
            raise TypeError("The supplied model must implement a predict_proba() function")
        if getattr(model, "list_classes", None) is None:
            raise TypeError("The supplied model must have a list_classes attribute")

        self.model = model
        self.model_conf = model_conf
        self.class_names = self.model.list_classes
        # Our explainers will explain a prediction for a given class / label
        # These atributes are set on the fly
        self.current_class_or_label_index = 0
        # Create the explainer
        self.explainer = LimeTextExplainer(class_names=self.class_names)

    def classifier_fn(self, content_list: list) -> np.ndarray:
        '''Function to get probabilities from a list of (not preprocessed) texts

        Args:
            content_list (list): texts to be considered
        Returns:
            np.array: probabilities
        '''
        # Get preprocessor
        if 'preprocess_str' in self.model_conf.keys():
            preprocess_str = self.model_conf['preprocess_str']
        else:
            preprocess_str = 'no_preprocess'
        preprocessor = preprocess.get_preprocessor(preprocess_str)
        # Preprocess
        content_prep = preprocessor(content_list)
        # Get probabilities
        return self.model.predict_proba(content_prep)

    def explain_instance(self, content: str, class_or_label_index: Union[int, None] = None,
                         max_features: int = 15, **kwargs):
        '''Explains a prediction

        This function calls the Lime module. It creates a linear model around the input text to evaluate
        the weight of each word in the final prediction.

        Args:
            content (str): Text to be explained
        Kwargs:
            class_or_label_index (int): for classification only. Class or label index to be considered.
            max_features (int): Maximum number of features (cf. Lime documentation)
        Returns:
            (?): An explanation object
        '''
        # Set index
        if class_or_label_index is not None:
            self.current_class_or_label_index = class_or_label_index
        else:
            self.current_class_or_label_index = 1  # Def to 1
        # Get explanations
        return self.explainer.explain_instance(content, self.classifier_fn, labels=(self.current_class_or_label_index,), num_features=max_features)

    def explain_instance_as_html(self, content: str, class_or_label_index: Union[int, None] = None,
                                 max_features: int = 15, **kwargs) -> str:
        '''Explains a prediction - returns an HTML object

        Args:
            content (str): Text to be explained
        Kwargs:
            class_or_label_index (int): for classification only. Class or label index to be considered.
            max_features (int): Maximum number of features (cf. Lime documentation)
        Returns:
            str: An HTML code with the explanation
        '''
        return self.explain_instance(content, class_or_label_index, max_features).as_html()

    def explain_instance_as_list(self, content: str, class_or_label_index: Union[int, None] = None,
                                 max_features: int = 15, **kwargs) -> list:
        '''Explains a prediction - returns a list object

        Args:
            content (str): Text to be explained
        Kwargs:
            class_or_label_index (int): for classification only. Class or label index to be considered.
            max_features (int): Maximum number of features (cf. Lime documentation)
        Returns:
            list: List of tuples with words and corresponding weights
        '''
        explanation = self.explain_instance(content, class_or_label_index, max_features)
        # Return as list for selected class or label
        return explanation.as_list(label=self.current_class_or_label_index)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.error("This script is not stand alone but belongs to a package that has to be imported.")
