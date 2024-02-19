# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "delivery_carrier", "default_carrier_id"):
        openupgrade.rename_fields(
            env,
            [
                (
                    "rma.operation",
                    "rma_operation",
                    "default_carrier_id",
                    "default_carrier_out_id",
                )
            ],
        )
