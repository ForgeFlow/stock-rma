# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT


class RmaMakePutAway(models.TransientModel):
    _name = "rma_make_put_away.wizard"
    _description = "Wizard to create put_away from rma lines"

    item_ids = fields.One2many(
        comodel_name="rma_make_put_away_item.wizard",
        inverse_name="wiz_id",
        string="Items",
    )

    @api.returns("rma.order.line")
    def _prepare_item(self, line):
        values = {
            "product_id": line.product_id.id,
            "product_qty": line.product_qty,
            "location_id": line.operation_id.put_away_location_id.id,
            "uom_id": line.uom_id.id,
            "qty_to_put_away": line.qty_to_put_away,
            "line_id": line.id,
            "rma_id": line.rma_id and line.rma_id.id or False,
        }
        return values

    @api.model
    def default_get(self, fields_list):
        """Default values for wizard, if there is more than one supplier on
        lines the supplier field is empty otherwise is the unique line
        supplier.
        """
        context = self._context.copy()
        res = super(RmaMakePutAway, self).default_get(fields_list)
        rma_line_obj = self.env["rma.order.line"]
        rma_line_ids = self.env.context["active_ids"] or []
        active_model = self.env.context["active_model"]

        if not rma_line_ids:
            return res
        assert active_model == "rma.order.line", "Bad context propagation"

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        res["item_ids"] = items
        context.update({"items_ids": items})
        return res

    def _create_put_away(self):
        """Method called when the user clicks on create picking"""
        procurements = []
        errors = []
        for item in self.item_ids:
            line = item.line_id
            if line.state != "approved":
                raise ValidationError(_("RMA %s is not approved") % line.name)
            procurement = self._prepare_procurement(item)
            procurements.append(procurement)
        try:
            self.env["procurement.group"].run(procurements)
        except UserError as error:
            errors.append(error.args[0])
        if errors:
            raise UserError("\n".join(errors))
        return procurements

    def action_create_put_away(self):
        self._create_put_away()
        action = self.item_ids.line_id.action_view_put_away_transfers()
        return action

    @api.model
    def _get_procurement_data(self, item):
        line = item.line_id
        route = line.operation_id.put_away_route_id
        if not route:
            raise ValidationError(_("No route specified"))
        procurement_data = {
            "name": line.rma_id and line.rma_id.name or line.name,
            "origin": line.name,
            "date_planned": time.strftime(DT_FORMAT),
            "product_id": item.product_id.id,
            "product_qty": item.product_qty,
            "qty_to_put_away": item.product_qty,
            "product_uom": line.product_id.product_tmpl_id.uom_id.id,
            "location_id": item.location_id.id,
            "rma_line_id": line.id,
            "route_ids": route,
            "company_id": line.company_id,
            "is_rma_put_away": True,
        }
        return procurement_data

    @api.model
    def _prepare_procurement(self, item):
        line = item.line_id
        values = self._get_procurement_data(item)
        values = dict(
            values, rma_line_id=item.line_id.id, rma_id=item.line_id.rma_id.id
        )
        procurement = self.env["procurement.group"].Procurement(
            item.line_id.product_id,
            item.product_qty,
            item.line_id.product_id.product_tmpl_id.uom_id,
            item.location_id,
            values.get("origin"),
            values.get("origin"),
            line.company_id,
            values,
        )
        return procurement


class RmaMakePutAwayItem(models.TransientModel):
    _name = "rma_make_put_away_item.wizard"
    _description = "Items to Put Away"

    wiz_id = fields.Many2one("rma_make_put_away.wizard", string="Wizard", required=True)
    line_id = fields.Many2one(
        "rma.order.line", string="RMA order Line", ondelete="cascade"
    )
    rma_id = fields.Many2one("rma.order", related="line_id.rma_id", string="RMA Group")
    product_id = fields.Many2one("product.product", string="Product")
    product_qty = fields.Float(
        related="line_id.product_qty",
        string="Quantity Ordered",
        copy=False,
        digits="Product Unit of Measure",
    )
    location_id = fields.Many2one("stock.location", string="Destination Location")
    qty_to_put_away = fields.Float(
        string="Quantity To put away", digits="Product Unit of Measure"
    )
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
