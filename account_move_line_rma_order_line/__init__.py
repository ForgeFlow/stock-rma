from . import models

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    api.Environment(cr, SUPERUSER_ID, {})
