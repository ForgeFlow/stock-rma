# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class RmaLineMakeRepair(models.TransientModel):
    _name = "rma.order.line.make.repair"
    _description = "Make Repair Order from RMA Line"

    item_ids = fields.One2many(
        comodel_name="rma.order.line.make.repair.item",
        inverse_name="wiz_id",
        string="Items",
    )

    @api.model
    def _prepare_item(self, line):
        return {
            "line_id": line.id,
            "product_id": line.product_id.id,
            "product_qty": line.qty_to_repair,
            "rma_id": line.rma_id.id,
            "out_route_id": line.out_route_id.id,
            "product_uom_id": line.uom_id.id,
            "partner_id": line.partner_id.id,
            "picking_type_id": line.operation_id.repair_picking_type_id.id,
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
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
        return res

    def create_repair_procurement_condition_applies(self, rma_line, repair):
        return (
            rma_line.location_id
            != repair.picking_type_id.default_product_location_src_id
        )

    def make_repair_order(self):
        self.ensure_one()
        res = []
        repair_obj = self.env["repair.order"]
        for item in self.item_ids:
            rma_line = item.line_id
            data = item._prepare_repair_order(rma_line)
            repair = repair_obj.create(data)
            res.append(repair.id)
            if self.create_repair_procurement_condition_applies(rma_line, repair):
                item._run_procurement(
                    rma_line.operation_id.repair_route_id,
                    repair.picking_type_id.default_product_location_src_id,
                )

        return {
            "domain": [("id", "in", res)],
            "name": self.env._("Repairs"),
            "view_mode": "list,form",
            "res_model": "repair.order",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }


class RmaLineMakeRepairItem(models.TransientModel):
    _name = "rma.order.line.make.repair.item"
    _description = "RMA Line Make Repair Item"

    @api.constrains("product_qty")
    def _check_product_qty(self):
        for rec in self:
            if rec.product_qty <= 0.0:
                raise ValidationError(self.env._("Quantity must be positive."))

    wiz_id = fields.Many2one(
        comodel_name="rma.order.line.make.repair", string="Wizard", ondelete="cascade"
    )
    line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA", required=True
    )
    rma_id = fields.Many2one(
        comodel_name="rma.order", related="line_id.rma_id", string="RMA Order"
    )
    product_id = fields.Many2one(
        comodel_name="product.product", string="Product", readonly=True
    )
    product_qty = fields.Float(string="Quantity to repair", digits="Product UoS")
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="UoM", readonly=True
    )
    out_route_id = fields.Many2one(
        comodel_name="stock.route",
        string="Outbound Route",
        domain=[("rma_selectable", "=", True)],
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        required=False,
        domain=[("customer_rank", ">=", 1)],
        readonly=True,
    )
    # Related becuase repairs are controlled by picking type since v18
    location_id = fields.Many2one(
        comodel_name="stock.location",
        related="picking_type_id.default_product_location_src_id",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="line_id.company_id",
    )
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Picking Type",
        domain="[('code', '=', 'repair_operation'), ('company_id', '=', company_id)]",
        required=True,
    )

    def _prepare_repair_order(self, rma_line):
        self.ensure_one()
        sellers = rma_line.product_id.seller_ids.filtered(
            lambda sel: sel.partner_id == rma_line.partner_id
        )
        seller_uom = sellers and sellers[0].product_uom_id or False
        if not seller_uom:
            seller_uom = rma_line.product_id.uom_id
        return {
            "product_id": rma_line.product_id.id,
            "partner_id": rma_line.partner_id.id,
            "product_qty": self.product_qty,
            "rma_line_id": rma_line.id,
            "product_uom": seller_uom.id,
            "company_id": rma_line.company_id.id,
            "picking_type_id": self.picking_type_id.id,
            "location_id": self.picking_type_id.default_location_dest_id.id,
            "lot_id": rma_line.lot_id.id,
        }

    def _run_procurement(self, route, dest_location):
        procurements = []
        errors = []
        procurement = self._prepare_procurement(route, dest_location)
        procurements.append(procurement)
        try:
            self.env["stock.rule"].with_context(picking_type="internal").run(
                procurements,
                raise_user_error=True,
            )
        except UserError as error:
            errors.append(error.args[0])
        if errors:
            raise UserError("\n".join(errors))
        return procurements

    def find_stock_reference(self):
        if self.line_id.rma_id:
            return self.env["stock.reference"].search(
                [("rma_id", "=", self.line_id.rma_id.id)], limit=1
            )
        else:
            return self.env["stock.reference"].search(
                [("rma_line_id", "=", self.line_id.id)], limit=1
            )

    def _create_stock_reference(self):
        ref_data = {
            "name": self.line_id.rma_id.name or self.line_id.name,
            "rma_id": self.line_id.rma_id.id if self.line_id.rma_id else False,
            "rma_line_id": self.line_id.id if not self.line_id.rma_id else False,
        }
        return self.env["stock.reference"].create(ref_data)

    @api.model
    def _get_procurement_data(self, route, dest_location):
        if not route:
            raise ValidationError(self.env._("No route specified"))
        ref = self.find_stock_reference()
        if not ref:
            ref = self._create_stock_reference()
        values = {
            "name": self.line_id.name,
            "origin": self.line_id.name,
            "date_planned": fields.Datetime.now(),
            "location_id": dest_location.id,
            "route_ids": route,
            "stock_reference_id": ref.id,
            "rma_line_id": self.line_id.id,
            "is_rma_repair_transfer": True,
            "partner_id": self.line_id.partner_id,
        }
        return values

    @api.model
    def _prepare_procurement(self, route, dest_location):
        values = self._get_procurement_data(route, dest_location)

        procurement = self.env["stock.rule"].Procurement(
            self.product_id,
            self.product_qty,
            self.product_id.uom_id,
            dest_location,
            values["origin"],
            values["origin"],
            self.env.company,
            values,
        )
        return procurement
