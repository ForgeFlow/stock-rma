import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT


class RmaMakePutAway(models.TransientModel):
    _name = "rma_make_put_away.wizard"
    _description = "Wizard to create put away from rma lines"

    item_ids = fields.One2many(
        comodel_name="rma_make_put_away.wizard.item",
        inverse_name="wiz_id",
        string="Items",
    )

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
            procurement = self._create_procurement(item, picking_type)
            procurements.extend(procurement)
        return procurements

    def action_create_put_away(self):
        self._create_put_away()
        action = self.item_ids.line_id.action_view_in_shipments()
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
        warehouse = line.operation_id.internal_warehouse_id
        route = line.operation_id.internal_route_id
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
#            "partner_id": delivery_address_id.id,
            "product_uom": line.product_id.product_tmpl_id.uom_id.id,
#            "location_id": location,
            "rma_line_id": line.id,
            "route_ids": route,
            "company_id": line.company_id
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

    def _get_procurement_group_data_put_away(self, item):
        group_data = {
            "partner_id": item.line_id.partner_id.id,
            "name": item.line_id.rma_id.name or item.line_id.name,
            "rma_id": item.line_id.rma_id and item.line_id.rma_id.id or False,
            "rma_line_id": item.line_id.id if not item.line_id.rma_id else False,
        }
        return group_data


class RmaMakePutAwayItem(models.TransientModel):
    _name = "rma_make_put_away.wizard.item"
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
    qty_to_receive = fields.Float(
        string="Quantity to Receive", digits="Product Unit of Measure"
    )
    qty_to_deliver = fields.Float(
        string="Quantity To Deliver", digits="Product Unit of Measure"
    )
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")



