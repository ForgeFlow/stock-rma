# Copyright (C) 2025 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openupgradelib import openupgrade  # pylint: disable=W7936

_field_renames = [
    ("stock.move", "stock_move", "forced_lot_id", "restrict_lot_id"),
]


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    for field in _field_renames:
        if openupgrade.table_exists(cr, field[1]) and openupgrade.column_exists(
            cr, field[1], field[2]
        ):
            env.cr.execute(
                "UPDATE stock_move "
                "SET restrict_lot_id = forced_lot_id "
                "WHERE restrict_lot_id is NULL AND forced_lot is NOT NULL"
            )
