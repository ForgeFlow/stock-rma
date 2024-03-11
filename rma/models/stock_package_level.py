from odoo import models


class StockPackageLevel(models.Model):

    _inherit = "stock.package_level"

    def write(self, values):
        ctx = self.env.context.copy()
        if (
            len(self) == 1
            and "location_dest_id" in values
            and self.location_dest_id.id == values.get("location_dest_id")
        ):
            ctx.update(
                {
                    "bypass_reservation_update": True,
                }
            )
        return super(StockPackageLevel, self.with_context(**ctx)).write(values)
