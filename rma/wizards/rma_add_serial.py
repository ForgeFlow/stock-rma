# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaAddSerialWiz(models.TransientModel):
    _name = "rma.add.serial.wiz"
    _description = "Wizard to add rma lines from Serial/Lot numbers"

    rma_id = fields.Many2one(
        comodel_name="rma.order", string="RMA Order", readonly=True, ondelete="cascade"
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", readonly=True
    )
    partner_shipping_id = fields.Many2one(
        string="Deliver To",
        comodel_name="res.partner",
    )
    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Lots/Serials selected",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        rma_obj = self.env["rma.order"]
        rma_id = self.env.context["active_ids"] or []
        active_model = self.env.context["active_model"]
        if not rma_id:
            return res
        assert active_model == "rma.order", "Bad context propagation"

        rma = rma_obj.browse(rma_id)
        res["rma_id"] = rma.id
        res["partner_id"] = rma.partner_id.id
        return res

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update(
                {
                    "partner_shipping_id": False,
                }
            )
            return

        self = self.with_company(self.rma_id.company_id)
        addr = self.partner_id.address_get(["delivery"])
        self.update(
            {
                "partner_shipping_id": addr["delivery"],
            }
        )

    def _prepare_rma_line_from_lot_vals(self, lot):
        if self.env.context.get("customer"):
            operation = (
                lot.product_id.rma_customer_operation_id
                or lot.product_id.categ_id.rma_customer_operation_id
            )
        else:
            operation = (
                lot.product_id.rma_supplier_operation_id
                or lot.product_id.categ_id.rma_supplier_operation_id
            )
        if not operation:
            operation = self.env["rma.operation"].search(
                [("type", "=", self.rma_id.type)], limit=1
            )
            if not operation:
                raise ValidationError(_("Please define an operation first"))

        if not operation.in_route_id or not operation.out_route_id:
            route = self.env["stock.route"].search(
                [("rma_selectable", "=", True)], limit=1
            )
            if not route:
                raise ValidationError(_("Please define an RMA route"))

        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env["stock.warehouse"].search(
                [
                    ("company_id", "=", self.rma_id.company_id.id),
                    ("lot_rma_id", "!=", False),
                ],
                limit=1,
            )
            if not warehouse:
                raise ValidationError(
                    _("Please define a warehouse with a default RMA location")
                )

        product_qty = 1  # serial
        if lot.product_id.tracking == "lot":
            # TODO: improve logic, allow to specify qty?
            product_qty = 1

        vals = {
            "partner_id": self.partner_id.id,
            "product_id": lot.product_id.id,
            "lot_id": lot.id,
            "uom_id": lot.product_id.uom_id.id,
            "operation_id": operation.id,
            "product_qty": product_qty,
            "delivery_address_id": self.partner_shipping_id.id or self.partner_id.id,
            "rma_id": self.rma_id.id,
            "receipt_policy": operation.receipt_policy,
            "delivery_policy": operation.delivery_policy,
            "in_warehouse_id": operation.in_warehouse_id.id or warehouse.id,
            "out_warehouse_id": operation.out_warehouse_id.id or warehouse.id,
            "in_route_id": operation.in_route_id.id or route.id,
            "out_route_id": operation.out_route_id.id or route.id,
            "location_id": (
                operation.location_id.id
                or operation.in_warehouse_id.lot_rma_id.id
                or warehouse.lot_rma_id.id
            ),
        }
        return vals

    def action_confirm(self):
        rma_line_obj = self.env["rma.order.line"]
        existing_lots = self.rma_id.mapped("rma_line_ids.lot_id")
        for lot in self.lot_ids:
            if lot in existing_lots:
                raise ValidationError(
                    _("Lot/Serial Number %s already added.") % lot.name
                )

            vals = self._prepare_rma_line_from_lot_vals(lot)
            rec = rma_line_obj.create(vals)
            # Ensure that configuration on the operation is applied (like
            #  policies).
            # TODO MIG: in v16 the usage of such onchange can be removed in
            #  favor of (pre)computed stored editable fields for all policies
            #  and configuration in the RMA operation.
            rec._onchange_operation_id()
        return {"type": "ir.actions.act_window_close"}
