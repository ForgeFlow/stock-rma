# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
import logging

_logger = logging.getLogger(__name__)


def _update_rma_operations(cr):
    _logger.info(
        "Updating rma operations to preset in_force_same_lot and out_force_same_lot"
    )
    cr.execute(
        """
        UPDATE rma_operation
        SET in_force_same_lot=True
        WHERE type='customer';
    """
    )
    cr.execute(
        """
        UPDATE rma_operation
        SET out_force_same_lot=True
        WHERE type='supplier';
    """
    )


def migrate(cr, version):
    _update_rma_operations(cr)
