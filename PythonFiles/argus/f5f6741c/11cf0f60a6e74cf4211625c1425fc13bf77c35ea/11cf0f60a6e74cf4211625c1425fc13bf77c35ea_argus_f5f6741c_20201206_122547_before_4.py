import numbers
from pathlib import Path
from typing import Iterable, Optional, List, Union, Dict

import torch

from argus.model.build import BuildModel
from argus.engine import Engine, State
from argus.callbacks import Callback, on_epoch_complete
from argus.callbacks.logging import metrics_logging
from argus.metrics.metric import Metric, METRIC_REGISTRY
from argus.metrics.loss import Loss
from argus.utils import deep_to, deep_detach


def _attach_callbacks(engine, callbacks):
    if callbacks is not None:
        for callback in callbacks:
            if isinstance(callback, Callback):
                callback.attach(engine)
            else:
                raise TypeError(
                    f"Expected callback type {Callback}, got {type(callback)}"
                )


def _attach_metrics(engine, metrics):
    for metric in metrics:
        if isinstance(metric, str):
            if metric in METRIC_REGISTRY:
                metric = METRIC_REGISTRY[metric]()
            else:
                raise ValueError(f"Metric '{metric}' not found in scope")
        if isinstance(metric, Metric):
            metric.attach(engine)
        else:
            raise TypeError(
                f"Expected metric type {Metric} or str, got {type(metric)}"
            )


class Model(BuildModel):
    """Argus model is an abstraction of a trainer/predictor that uses:

    Attributes:
        nn_module (torch.nn.Module): PyTorch model as :class:`torch.nn.Module`.
        optimizer (torch.optim.Optimizer): Optimizer as
            :class:`torch.optim.Optimizer`.
        loss (torch.nn.Module): Loss function as :class:`torch.nn.Module`.
        device: (torch.device): device as :class:`torch.torch.device`.
        prediction_transform (Callable): postprocessing function of predictions
            as :class:`Callable` function or object.

    Args:
        params (dict): A model parameters.

    Examples:

        One can use several ways to initialize :class:`argus.model.Model`:

        1. Set parameters for each part of the model directly:

        .. code-block:: python

            class MnistModel(argus.Model):
                nn_module = Net  # torch.nn.Module
                optimizer = torch.optim.SGD
                loss = torch.nn.CrossEntropyLoss

            params = {
                'nn_module': {'n_classes': 10, 'p_dropout': 0.1},
                'optimizer': {'lr': 0.01},
                'device': 'cpu'
            }

            model = MnistModel(params)

        2. Set components of the model from multiple options using two
        elements tuples (component name, the component init arguments):

        .. code-block:: python

            from torchvision.models import resnet18

            class FlexModel(argus.Model):
                nn_module = {
                    'net': Net,
                    'resnet18': resnet18
                }

            params = {
                'nn_module': ('resnet18', {
                    'pretrained': False,
                    'num_classes': 1
                }),
                'optimizer': ('Adam', {'lr': 0.01}),
                'loss': 'CrossEntropyLoss',
                'device': 'cuda'
            }

            model = FlexModel(params)

    """

    def __init__(self, params: dict):
        super().__init__(params)

    def train_step(self, batch, state: State) -> dict:
        """Perform a single train step.

        The method is used by :class:`argus.engine.Engine`.
        The train step includes input and target tensor transferring to the
        model device, forward pass, loss evaluation, backward pass, and the
        train batch prediction treating with a prediction_transform.

        Args:
            batch (tuple of 2 torch.Tensors: (input, target)): The input and
                target tensors to process.
            state (:class:`argus.engine.State`): The argus model state.

        Returns:
            dict: The train step results::

                {
                    'prediction': The train batch predictions,
                    'target': The train batch target data on the model device,
                    'loss': The loss function value
                }

        """
        self.train()
        self.optimizer.zero_grad()
        input, target = deep_to(batch, device=self.device, non_blocking=True)
        prediction = self.nn_module(input)
        loss = self.loss(prediction, target)
        loss.backward()
        self.optimizer.step()

        prediction = deep_detach(prediction)
        target = deep_detach(target)
        prediction = self.prediction_transform(prediction)
        return {
            'prediction': prediction,
            'target': target,
            'loss': loss.item()
        }

    def val_step(self, batch, state: State) -> dict:
        """Perform a single validation step.

        The method is used by :class:`argus.engine.Engine`.
        The validation step includes input and target tensor transferring to
        the model device, forward pass, loss evaluation, and the val batch
        prediction treating with a prediction_transform.

        Gradients calculation and the model weights update are omitted, which
        is the main difference with the :meth:`train_step`
        method.

        Args:
            batch (tuple of 2 torch.Tensors: (input, target)): The input data
                and target tensors to process.
            state (:class:`argus.engine.State`): The argus model state.

        Returns:
            dict: Default val step results::

                {
                    'prediction': The val batch predictions,
                    'target': The val batch target data on the model device,
                    'loss': The loss function value
                }

        """
        self.eval()
        with torch.no_grad():
            input, target = deep_to(
                batch, device=self.device, non_blocking=True)
            prediction = self.nn_module(input)
            loss = self.loss(prediction, target)
            prediction = self.prediction_transform(prediction)
            return {
                'prediction': prediction,
                'target': target,
                'loss': loss.item()
            }

    def fit(self,
            train_loader: Iterable,
            val_loader: Optional[Iterable] = None,
            num_epochs: int = 1,
            metrics: Optional[List[Union[Metric, str]]] = None,
            metrics_on_train: bool = False,
            callbacks: Optional[List[Callback]] = None,
            val_callbacks: Optional[List[Callback]] = None):
        """Train the argus model.

        The method attaches metrics and callbacks to the train and validation
        process, and performs training itself.

        Args:
            train_loader (Iterable): The train data loader.
            val_loader (Iterable, optional): The validation data loader.
                Defaults to `None`.
            num_epochs (int, optional): Number of training epochs to
                run. Defaults to 1.
            metrics (list of :class:`argus.metrics.Metric`, optional):
                List of metrics to evaluate. By default, the metrics are
                evaluated on the validation data (if any) only.
                Defaults to `None`.
            metrics_on_train (bool, optional): Evaluate the metrics on train
                data as well. Defaults to False.
            callbacks (list of :class:`argus.callbacks.Callback`, optional):
                List of callbacks to be attached to the training process.
                Defaults to `None`.
            val_callbacks (list of :class:`argus.callbacks.Callback`, optional):
                List of callbacks to be attached to the validation process.
                Defaults to `None`.

        """
        self._check_train_ready()
        metrics = [] if metrics is None else metrics

        train_engine = Engine(self.train_step, model=self,
                              logger=self.logger, phase='train')
        train_metrics = [Loss()] + metrics if metrics_on_train else [Loss()]
        _attach_metrics(train_engine, train_metrics)
        metrics_logging.attach(train_engine, train=True)

        if val_loader is not None:
            self.validate(val_loader, metrics, val_callbacks)
            val_engine = Engine(self.val_step, model=self,
                                logger=self.logger, phase='val')
            _attach_metrics(val_engine, [Loss()] + metrics)
            _attach_callbacks(val_engine, val_callbacks)

            @on_epoch_complete
            def validation_epoch(train_state, val_engine, val_loader):
                epoch = train_state.epoch
                val_state = val_engine.run(val_loader, epoch, epoch + 1)
                train_state.metrics.update(val_state.metrics)

            validation_epoch.attach(train_engine, val_engine, val_loader)
            metrics_logging.attach(train_engine, train=False)

        _attach_callbacks(train_engine, callbacks)
        train_engine.run(train_loader, 0, num_epochs)

    def validate(self,
                 val_loader: Optional[Iterable],
                 metrics: Optional[List[Metric]] = None,
                 callbacks: Optional[List[Callback]] = None) -> Dict[str, float]:
        """Perform a validation.

        Args:
            val_loader (Iterable): The validation data loader.
            metrics (list of :class:`argus.metrics.Metric`, optional):
                List of metrics to evaluate with the data. Defaults to `None`.
            callbacks (list of :class:`argus.callbacks.Callback`, optional):
                List of callbacks to be attached to the validation process.
                Defaults to `None`.

        Returns:
            dict: The metrics dictionary.

        """
        self._check_train_ready()
        metrics = [] if metrics is None else metrics
        val_engine = Engine(self.val_step, model=self,
                            logger=self.logger, phase='val')
        _attach_metrics(val_engine, [Loss()] + metrics)
        _attach_callbacks(val_engine, callbacks)
        metrics_logging.attach(val_engine, train=False, print_epoch=False)
        return val_engine.run(val_loader).metrics

    def set_lr(self, lr: Union[float, List[float]]):
        """Set the learning rate for the optimizer.

        The method allows setting individual learning rates for the optimizer
        parameter groups as well as setting even learning rate for all
        parameters.

        Args:
            lr (number or list/tuple of numbers): The learning rate to set. If
                a single number is provided, all parameter groups learning
                rates are set to the same value. In order to set individual
                learning rates for each parameter group, a list or tuple of
                values with the corresponding length should be provided.

        Raises:
            ValueError: If *lr* is a list or tuple and its length is not equal
                to the number of parameter groups.
            ValueError: If *lr* type is not a list, tuple, or number.
            AttributeError: If the model is not *train_ready* (i.e. not all
                attributes are set).

        """
        self._check_train_ready()
        param_groups = self.optimizer.param_groups
        if isinstance(lr, (list, tuple)):
            lrs = list(lr)
            if len(lrs) != len(param_groups):
                raise ValueError(f"Expected lrs length {len(param_groups)}, "
                                 f"got {len(lrs)}")
        elif isinstance(lr, numbers.Number):
            lrs = [lr] * len(param_groups)
        else:
            raise ValueError(f"Expected lr type list, tuple or number, "
                             f"got {type(lr)}")
        for group_lr, param_group in zip(lrs, param_groups):
            param_group['lr'] = group_lr

    def get_lr(self) -> Union[float, List[float]]:
        """Get the learning rate from the optimizer.

        It could be a single value or a list of values in the case of multiple
        parameter groups.

        Returns:
            (float or a list of floats): The learning rate value or a list of
            individual parameter groups learning rate values.

        """
        self._check_train_ready()
        lrs = []
        for param_group in self.optimizer.param_groups:
            lrs.append(param_group['lr'])
        if len(lrs) == 1:
            return lrs[0]
        return lrs

    def save(self, file_path: Union[str, Path], optimizer_state: bool = False):
        """Save the argus model into a file.

        The argus model is saved as a dict::

            {
                'model_name': Name of the argus model,
                'params': Argus model parameters dict,
                'nn_state_dict': torch nn_module.state_dict(),
                'optimizer_state_dict': torch optimizer.state_dict()
            }

        The *state_dict* is always transferred to CPU before saving.

        Args:
            file_path (str): Path to the argus model file.
            optimizer_state (bool): Save optimizer state. Defaults to False.

        """
        nn_module = self.get_nn_module()
        state = {
            'model_name': self.__class__.__name__,
            'params': self.params,
            'nn_state_dict': deep_to(nn_module.state_dict(), 'cpu')
        }
        if optimizer_state and self.optimizer is not None:
            state['optimizer_state_dict'] = deep_to(
                self.optimizer.state_dict(), 'cpu'
            )
        torch.save(state, file_path)
        self.logger.info(f"Model saved to '{file_path}'")

    def predict(self, input):
        """Make a prediction with the given input.

        The prediction process consists of the input tensor transferring to the
        model device, forward pass of the nn_module in *eval* mode and
        application of the prediction_transform to the raw prediction output.

        Args:
            input (torch.Tensor): The input tensor to predict with. It will be
                transferred to the model device. The user is responsible for
                ensuring that the input tensor shape and type match the model.

        Returns:
            torch.Tensor or other type: Predictions as the result of the
                prediction_transform application.

        """
        self._check_predict_ready()
        with torch.no_grad():
            self.eval()
            input = deep_to(input, self.device)
            prediction = self.nn_module(input)
            prediction = self.prediction_transform(prediction)
            return prediction

    def train(self):
        """Set the nn_module into train mode."""
        if not self.nn_module.training:
            self.nn_module.train()

    def eval(self):
        """Set the nn_module into eval mode."""
        if self.nn_module.training:
            self.nn_module.eval()
