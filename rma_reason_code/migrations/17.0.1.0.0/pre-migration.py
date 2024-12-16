from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "rma_reason_code", "type"):
        openupgrade.rename_fields(
            env,
            [
                (
                    "rma.reason.code",
                    "rma_reason_code",
                    "type",
                    "rma_type",
                )
            ],
        )
