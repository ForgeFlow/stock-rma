# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    lot_rma_id = fields.Many2one(
        comodel_name="stock.location", string="RMA Location"
    )  # not readonly to have the possibility to edit location and
    # propagate to rma rules (add a auto-update when writing this field?)
    rma_cust_out_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="RMA Customer out Type", readonly=True
    )
    rma_sup_out_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="RMA Supplier out Type", readonly=True
    )
    rma_cust_in_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="RMA Customer in Type", readonly=True
    )
    rma_sup_in_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="RMA Supplier in Type", readonly=True
    )
    rma_in_this_wh = fields.Boolean(
        string="RMA in this Warehouse",
        help="If set, it will create RMA location, picking types and routes "
        "for this warehouse.",
    )
    rma_customer_pull_id = fields.Many2one(
        comodel_name="stock.route",
        string="RMA Customer Route",
    )
    rma_supplier_pull_id = fields.Many2one(
        comodel_name="stock.route",
        string="RMA Supplier Route",
    )

    @api.returns("self")
    def _get_all_routes(self):
        routes = super()._get_all_routes()
        routes |= self.rma_customer_pull_id
        routes |= self.rma_supplier_pull_id
        return routes

    def _get_rma_types(self):
        return [
            self.rma_cust_out_type_id,
            self.rma_sup_out_type_id,
            self.rma_cust_in_type_id,
            self.rma_sup_in_type_id,
        ]

    def _rma_types_available(self):
        self.ensure_one()
        rma_types = self._get_rma_types()
        for r_type in rma_types:
            if not r_type:
                return False
        return True

    def write(self, vals):
        if "rma_in_this_wh" in vals:
            if vals.get("rma_in_this_wh"):
                for wh in self:
                    # RMA location:
                    if not wh.lot_rma_id:
                        wh.lot_rma_id = self.env["stock.location"].create(
                            {
                                "name": "RMA",
                                "usage": "internal",
                                "location_id": wh.view_location_id.id,
                                "company_id": wh.company_id.id,
                                "return_location": True,
                            }
                        )
                    # RMA types
                    if not wh._rma_types_available():
                        wh._create_rma_picking_types()
                    else:
                        for r_type in wh._get_rma_types():
                            if r_type:
                                r_type.active = True
                    # RMA routes:
                    wh._create_rma_pull()
            else:
                for wh in self:
                    for r_type in wh._get_rma_types():
                        if r_type:
                            r_type.active = False
                # Unlink rules:
                self.mapped("rma_customer_pull_id").active = False
                self.mapped("rma_supplier_pull_id").active = False
        return super(StockWarehouse, self).write(vals)

    def _create_rma_picking_types(self):
        picking_type_obj = self.env["stock.picking.type"]
        customer_loc, supplier_loc = self._get_partner_locations()
        for wh in self:
            other_pick_type = picking_type_obj.search(
                [("warehouse_id", "=", wh.id)], order="sequence desc", limit=1
            )
            color = other_pick_type.color if other_pick_type else 0
            max_sequence = other_pick_type and other_pick_type.sequence or 0
            # create rma_cust_out_type_id:
            rma_cust_out_type_id = picking_type_obj.create(
                {
                    "name": _("Customer RMA Deliveries"),
                    "warehouse_id": wh.id,
                    "code": "outgoing",
                    "use_create_lots": True,
                    "use_existing_lots": False,
                    "sequence_id": self.env.ref("rma.seq_picking_type_rma_cust_out").id,
                    "default_location_src_id": wh.lot_rma_id.id,
                    "default_location_dest_id": customer_loc.id,
                    "sequence": max_sequence,
                    "color": color,
                    "sequence_code": "RMA → Customer",
                }
            )
            # create rma_sup_out_type_id:
            rma_sup_out_type_id = picking_type_obj.create(
                {
                    "name": _("Supplier RMA Deliveries"),
                    "warehouse_id": wh.id,
                    "code": "outgoing",
                    "use_create_lots": True,
                    "use_existing_lots": False,
                    "sequence_id": self.env.ref("rma.seq_picking_type_rma_sup_out").id,
                    "default_location_src_id": wh.lot_rma_id.id,
                    "default_location_dest_id": supplier_loc.id,
                    "sequence": max_sequence,
                    "color": color,
                    "sequence_code": "Customer → RMA",
                }
            )
            # create rma_cust_in_type_id:
            rma_cust_in_type_id = picking_type_obj.create(
                {
                    "name": _("Customer RMA Receipts"),
                    "warehouse_id": wh.id,
                    "code": "incoming",
                    "use_create_lots": True,
                    "use_existing_lots": False,
                    "sequence_id": self.env.ref("rma.seq_picking_type_rma_cust_in").id,
                    "default_location_src_id": customer_loc.id,
                    "default_location_dest_id": wh.lot_rma_id.id,
                    "sequence": max_sequence,
                    "color": color,
                    "sequence_code": "RMA -> Supplier",
                }
            )
            # create rma_sup_in_type_id:
            rma_sup_in_type_id = picking_type_obj.create(
                {
                    "name": _("Supplier RMA Receipts"),
                    "warehouse_id": wh.id,
                    "code": "incoming",
                    "use_create_lots": True,
                    "use_existing_lots": False,
                    "sequence_id": self.env.ref("rma.seq_picking_type_rma_sup_in").id,
                    "default_location_src_id": supplier_loc.id,
                    "default_location_dest_id": wh.lot_rma_id.id,
                    "sequence": max_sequence,
                    "color": color,
                    "sequence_code": "Supplier -> RMA",
                }
            )
            wh.write(
                {
                    "rma_cust_out_type_id": rma_cust_out_type_id.id,
                    "rma_sup_out_type_id": rma_sup_out_type_id.id,
                    "rma_cust_in_type_id": rma_cust_in_type_id.id,
                    "rma_sup_in_type_id": rma_sup_in_type_id.id,
                }
            )
        return True

    def get_rma_route_customer(self):
        self.ensure_one()
        customer_loc, _ = self._get_partner_locations()
        rma_rules = [
            {
                "name": self.name + ": Customer RMA",
                "rma_selectable": True,
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self._format_rulename(
                                self, customer_loc, self.lot_rma_id.name
                            ),
                            "action": "pull",
                            "warehouse_id": self.id,
                            "company_id": self.company_id.id,
                            "location_src_id": customer_loc.id,
                            "location_dest_id": self.lot_rma_id.id,
                            "procure_method": "make_to_stock",
                            "picking_type_id": self.rma_cust_in_type_id.id,
                            "active": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": self._format_rulename(
                                self, self.lot_rma_id, customer_loc.name
                            ),
                            "action": "pull",
                            "warehouse_id": self.id,
                            "company_id": self.company_id.id,
                            "location_src_id": self.lot_rma_id.id,
                            "location_dest_id": customer_loc.id,
                            "procure_method": "make_to_stock",
                            "picking_type_id": self.rma_cust_out_type_id.id,
                            "active": True,
                        },
                    ),
                ],
            }
        ]
        return rma_rules

    def get_rma_route_supplier(self):
        self.ensure_one()
        _, supplier_loc = self._get_partner_locations()
        rma_route = [
            {
                "name": self.name + ": Supplier RMA",
                "rma_selectable": True,
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self._format_rulename(
                                self, supplier_loc, self.lot_rma_id.name
                            ),
                            "action": "pull",
                            "warehouse_id": self.id,
                            "company_id": self.company_id.id,
                            "location_src_id": supplier_loc.id,
                            "location_dest_id": self.lot_rma_id.id,
                            "procure_method": "make_to_stock",
                            "picking_type_id": self.rma_sup_in_type_id.id,
                            "active": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": self._format_rulename(
                                self, self.lot_rma_id, supplier_loc.name
                            ),
                            "action": "pull",
                            "warehouse_id": self.id,
                            "company_id": self.company_id.id,
                            "location_src_id": self.lot_rma_id.id,
                            "location_dest_id": supplier_loc.id,
                            "procure_method": "make_to_stock",
                            "picking_type_id": self.rma_sup_out_type_id.id,
                            "active": True,
                        },
                    ),
                ],
            }
        ]
        return rma_route

    def _create_rma_pull(self):
        route_obj = self.env["stock.route"]
        for wh in self:
            if not wh.rma_customer_pull_id:
                wh.rma_customer_pull_id = (
                    route_obj.create(self.get_rma_route_customer())
                    if wh
                    not in self.env.ref("rma.route_rma_customer").rule_ids.mapped(
                        "warehouse_id"
                    )
                    else self.env.ref("rma.route_rma_customer")
                )

            if not wh.rma_supplier_pull_id:
                wh.rma_supplier_pull_id = (
                    route_obj.create(self.get_rma_route_supplier())
                    if wh
                    not in self.env.ref("rma.route_rma_supplier").rule_ids.mapped(
                        "warehouse_id"
                    )
                    else self.env.ref("rma.route_rma_supplier")
                )
        return True


class StockLocationRoute(models.Model):
    _inherit = "stock.route"

    rma_selectable = fields.Boolean(string="Selectable on RMA Lines")
