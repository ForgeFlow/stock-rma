# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT, float_compare


class RmaMakePicking(models.TransientModel):
    _name = "rma_make_picking.wizard"
    _description = "Wizard to create pickings from rma lines"

    @api.returns("rma.order.line")
    def _prepare_item(self, line):
        values = {
            "product_id": line.product_id.id,
            "product_qty": line.product_qty,
            "uom_id": line.uom_id.id,
            "qty_to_receive": line.qty_to_receive,
            "qty_to_deliver": line.qty_to_deliver,
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
        res = super(RmaMakePicking, self).default_get(fields_list)
        rma_line_obj = self.env["rma.order.line"]
        rma_line_ids = self.env.context["active_ids"] or []
        active_model = self.env.context["active_model"]

        if not rma_line_ids:
            return res
        assert active_model == "rma.order.line", "Bad context propagation"

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        if len(lines.mapped("partner_id")) > 1:
            raise ValidationError(
                _(
                    "Only RMA lines from the same partner can be processed at "
                    "the same time"
                )
            )
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        res["item_ids"] = items
        context.update({"items_ids": items})
        return res

    item_ids = fields.One2many("rma_make_picking.wizard.item", "wiz_id", string="Items")

    def find_procurement_group(self, item):
        if item.line_id.rma_id:
            return self.env["procurement.group"].search(
                [("rma_id", "=", item.line_id.rma_id.id)]
            )
        else:
            return self.env["procurement.group"].search(
                [("rma_line_id", "=", item.line_id.id)]
            )

    def _get_procurement_group_data(self, item):
        group_data = {
            "partner_id": item.line_id.partner_id.id,
            "name": item.line_id.rma_id.name or item.line_id.name,
            "rma_id": item.line_id.rma_id and item.line_id.rma_id.id or False,
        }
        if not item.line_id.rma_id:
            group_data["rma_line_id"] = item.line_id and item.line_id.id or False
        return group_data

    @api.model
    def _get_address(self, item):
        if item.line_id.customer_to_supplier:
            delivery_address = item.line_id.supplier_address_id
        elif item.line_id.supplier_to_customer:
            delivery_address = item.line_id.customer_address_id
        elif item.line_id.delivery_address_id:
            delivery_address = item.line_id.delivery_address_id
        elif item.line_id.partner_id:
            delivery_address = item.line_id.partner_id
        else:
            raise ValidationError(_("Unknown delivery address"))
        return delivery_address

    @api.model
    def _get_address_location(self, delivery_address_id, a_type):
        if a_type == "supplier":
            return delivery_address_id.property_stock_supplier
        elif a_type == "customer":
            return delivery_address_id.property_stock_customer

    @api.model
    def _get_procurement_data(self, item, group, qty, picking_type):
        line = item.line_id
        delivery_address_id = self._get_address(item)
        if picking_type == "incoming":
            if line.customer_to_supplier:
                location = self._get_address_location(delivery_address_id, "supplier")
            elif line.supplier_to_customer:
                location = self._get_address_location(delivery_address_id, "customer")
            else:
                location = line.location_id
            warehouse = line.in_warehouse_id
            route = line.in_route_id
        else:
            location = self._get_address_location(delivery_address_id, line.type)
            warehouse = line.out_warehouse_id
            route = line.out_route_id
        if not route:
            raise ValidationError(_("No route specified"))
        if not warehouse:
            raise ValidationError(_("No warehouse specified"))
        procurement_data = {
            "name": line.rma_id and line.rma_id.name or line.name,
            "group_id": group,
            "origin": group and group.name or line.name,
            "warehouse_id": warehouse,
            "date_planned": time.strftime(DT_FORMAT),
            "product_id": item.product_id,
            "product_qty": qty,
            "partner_id": delivery_address_id.id,
            "product_uom": line.product_id.product_tmpl_id.uom_id.id,
            "location_id": location,
            "rma_line_id": line.id,
            "route_ids": route,
        }
        return procurement_data

    @api.model
    def _create_procurement(self, item, picking_type):
        errors = []
        group = self.find_procurement_group(item)
        if not group:
            pg_data = self._get_procurement_group_data(item)
            group = self.env["procurement.group"].create(pg_data)
        if picking_type == "incoming":
            qty = item.qty_to_receive
        else:
            qty = item.qty_to_deliver
        values = self._get_procurement_data(item, group, qty, picking_type)
        product = item.line_id.product_id
        if float_compare(qty, 0, product.uom_id.rounding) != 1:
            raise ValidationError(
                _("No quantity to transfer on %s shipment of product %s.")
                % (_(picking_type), product.default_code or product.name)
            )
        # create picking
        procurements = []
        try:
            procurement = group.Procurement(
                item.line_id.product_id,
                qty,
                item.line_id.product_id.product_tmpl_id.uom_id,
                values.get("location_id"),
                values.get("origin"),
                values.get("origin"),
                self.env.company,
                values,
            )

            procurements.append(procurement)
            # Trigger a route check with a mutable in the context that can be
            # cleared after the first rule selection
            self.env["procurement.group"].with_context(rma_route_check=[True]).run(
                procurements
            )
        except UserError as error:
            errors.append(error.name)
        if errors:
            raise UserError("\n".join(errors))
        return procurements

    def _create_picking(self):
        """Method called when the user clicks on create picking"""
        picking_type = self.env.context.get("picking_type")
        procurements = []
        for item in self.item_ids:
            line = item.line_id
            if line.state != "approved":
                raise ValidationError(_("RMA %s is not approved") % line.name)
            if line.receipt_policy == "no" and picking_type == "incoming":
                raise ValidationError(_("No shipments needed for this operation"))
            if line.delivery_policy == "no" and picking_type == "outgoing":
                raise ValidationError(_("No deliveries needed for this operation"))
            procurement = self._create_procurement(item, picking_type)
            procurements.extend(procurement)
        return procurements

    def _is_final_step(self, move):
        """This function helps to know if wizard is called to finish process of rma,
        customer is delivery return, and supplier is receipt return"""
        if (
            move.rma_line_id.type == "customer"
            and self.env.context.get("picking_type") == "outgoing"
        ):
            return True
        if (
            move.rma_line_id.type == "supplier"
            and self.env.context.get("picking_type") == "incoming"
        ):
            return True
        return False

    def action_create_picking(self):
        self._create_picking()
        move_line_model = self.env["stock.move.line"]
        picking_type = self.env.context.get("picking_type")
        if picking_type == "outgoing":
            pickings = self.mapped("item_ids.line_id")._get_out_pickings()
            action = self.item_ids.line_id.action_view_out_shipments()
        else:
            pickings = self.mapped("item_ids.line_id")._get_in_pickings()
            action = self.item_ids.line_id.action_view_in_shipments()
        # Force the reservation of the RMA specific lot for incoming shipments.
        # FIXME: still needs fixing, not reserving appropriate serials.
        for move in pickings.move_lines.filtered(
            lambda x: x.state not in ("draft", "cancel", "done", "waiting")
            and x.rma_line_id
            and x.product_id.tracking in ("lot", "serial")
            and x.rma_line_id.lot_id
        ):
            # Force the reservation of the RMA specific lot for incoming shipments.
            is_final_step = self._is_final_step(move)
            move.move_line_ids.unlink()
            reference_moves = (
                not is_final_step
                and move.rma_line_id._get_stock_move_reference()
                or self.env["stock.move"]
            )
            package = reference_moves.mapped("move_line_ids.result_package_id")
            quants = self.env["stock.quant"]._gather(
                move.product_id,
                move.location_id,
                lot_id=move.rma_line_id.lot_id,
                package_id=len(package) == 1 and package or False,
            )
            move_line_data = move._prepare_move_line_vals(
                reserved_quant=(len(quants) == 1) and quants or False
            )
            move_line_data.update(
                {
                    "qty_done": 0,
                }
            )
            if move.rma_line_id.lot_id and not quants:
                # CHECK ME: force al least has lot assigned if quant is not found
                move_line_data.update(
                    {
                        "lot_id": move.rma_line_id.lot_id.id,
                    }
                )
            if move.product_id.tracking == "serial":
                move.write(
                    {
                        "lot_ids": move.rma_line_id.lot_id.ids,
                    }
                )
                move_line_data.update(
                    {
                        "product_uom_qty": 1.0,
                    }
                )
                if move.move_line_ids:
                    move.move_line_ids.with_context(
                        bypass_reservation_update=True
                    ).write(
                        {
                            "lot_id": move_line_data.get("lot_id"),
                            "package_id": move_line_data.get("package_id"),
                            "result_package_id": move_line_data.get(
                                "result_package_id", False
                            ),
                            "product_uom_qty": 1.0,
                        }
                    )
                if (
                    len(quants) == 1
                    and quants.reserved_quantity == 0
                    and quants.quantity == 1
                    and quants.location_id.usage not in ("customer", "supplier")
                ):
                    quants.sudo().write(
                        {"reserved_quantity": quants.reserved_quantity + 1}
                    )
            elif move.product_id.tracking == "lot":
                if picking_type == "incoming":
                    qty = self.item_ids.filtered(
                        lambda x: x.line_id.id == move.rma_line_id.id
                    ).qty_to_receive
                else:
                    qty = self.item_ids.filtered(
                        lambda x: x.line_id.id == move.rma_line_id.id
                    ).qty_to_deliver
                move_line_data.update(
                    {
                        "product_uom_qty": qty if picking_type == "incoming" else 0,
                    }
                )
            if not move.move_line_ids:
                move_line_model.create(move_line_data)
            pickings.with_context(force_no_bypass_reservation=True).action_assign()
        return action

    def action_cancel(self):
        return {"type": "ir.actions.act_window_close"}


class RmaMakePickingItem(models.TransientModel):
    _name = "rma_make_picking.wizard.item"
    _description = "Items to receive"

    wiz_id = fields.Many2one("rma_make_picking.wizard", string="Wizard", required=True)
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
    qty_to_receive = fields.Float(
        string="Quantity to Receive", digits="Product Unit of Measure"
    )
    qty_to_deliver = fields.Float(
        string="Quantity To Deliver", digits="Product Unit of Measure"
    )
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
