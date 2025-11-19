# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Repairs are controlled by picking types since v18.

    ``repair_location_id`` on the operation is replaced by
    ``repair_picking_type_id``: the picking type whose default product source
    location is the old repair location. Operations without a matching picking
    type are left empty, to be set manually.

    ``repair.order.under_warranty`` is the native stored field again instead of
    a related to the RMA line, so the stale values are refreshed from the line.
    """
    openupgrade.add_columns(
        env,
        [
            (
                "rma.operation",
                "repair_picking_type_id",
                "many2one",
                None,
                "rma_operation",
            )
        ],
    )
    if openupgrade.column_exists(env.cr, "rma_operation", "repair_location_id"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE rma_operation operation
            SET repair_picking_type_id = (
                SELECT picking_type.id FROM stock_picking_type picking_type
                WHERE picking_type.code = 'repair_operation'
                AND picking_type.default_product_location_src_id =
                    operation.repair_location_id
                ORDER BY picking_type.id LIMIT 1
            )
            WHERE operation.repair_location_id IS NOT NULL
            """,
        )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE repair_order repair
        SET under_warranty = line.under_warranty
        FROM rma_order_line line
        WHERE repair.rma_line_id = line.id
        """,
    )
