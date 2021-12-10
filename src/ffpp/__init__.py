import logging

from .Printer import Printer  # noqa

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
out_handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(name)s : %(message)s'
)
out_handler.setFormatter(formatter)
LOG.addHandler(out_handler)
