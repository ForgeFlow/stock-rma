import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT


class RmaMakePutAway(models.TransientModel):
    _name = "rma_make_put_away.wizard"
    _description = "Wizard to create put away from rma lines"

    item_ids = fields.One2many("rma_make_picking.wizard.item", "wiz_id", string="Items")

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
        res = super(RmaMakePutAway, self).default_get(fields_list)
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

    def _create_put_away(self):
        """Method called when the user clicks on create picking"""
        picking_type = "internal"
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

    def action_create_put_away(self):
        self._create_put_away()
        move_line_model = self.env["stock.move.line"]
        picking_type = "internal"
        pickings = self.mapped("item_ids.line_id")._get_in_pickings()
        action = self.item_ids.line_id.action_view_in_shipments()
        if picking_type == "internal":
            # Force the reservation of the RMA specific lot for incoming shipments.
            # FIXME: still needs fixing, not reserving appropriate serials.
            for move in pickings.move_lines.filtered(
                lambda x: x.state not in ("draft", "cancel", "done")
                          and x.rma_line_id
                          and x.product_id.tracking in ("lot", "serial")
                          and x.rma_line_id.lot_id
            ):
                # Force the reservation of the RMA specific lot for incoming shipments.
                move.move_line_ids.unlink()
                if move.product_id.tracking == "serial":
                    move.write(
                        {
                            "lot_ids": [(6, 0, move.rma_line_id.lot_id.ids)],
                        }
                    )
                    move.move_line_ids.write(
                        {
                            "product_uom_qty": 1,
                            "qty_done": 0,
                        }
                    )
                elif move.product_id.tracking == "lot":
                    if picking_type == "internal":
                        qty = self.item_ids.filtered(
                            lambda x: x.line_id.id == move.rma_line_id.id
                        ).qty_to_receive
                    else:
                        qty = self.item_ids.filtered(
                            lambda x: x.line_id.id == move.rma_line_id.id
                        ).qty_to_deliver
                    move_line_data = move._prepare_move_line_vals()
                    move_line_data.update(
                        {
                            "lot_id": move.rma_line_id.lot_id.id,
                            "product_uom_id": move.product_id.uom_id.id,
                            "qty_done": 0,
                            "product_uom_qty": qty,
                        }
                    )
                    move_line_model.create(move_line_data)

            pickings.with_context(force_no_bypass_reservation=True).action_assign()
        return action

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
            "origin": line.name,
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
        qty = item.product_qty
        values = self._get_procurement_data(item, group, qty, picking_type)
        values = dict(values, rma_line_id=item.line_id, rma_id=item.line_id.rma_id)
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
            self.env["procurement.group"].run(procurements)
        except UserError as error:
            errors.append(error.name)
        if errors:
            raise UserError("\n".join(errors))
        return procurements

    def find_procurement_group(self, item):
        if item.line_id.rma_id:
            return self.env["procurement.group"].search(
                [("rma_id", "=", item.line_id.rma_id.id)]
            )
        else:
            return self.env["procurement.group"].search(
                [("rma_line_id", "=", item.line_id.id)]
            )
