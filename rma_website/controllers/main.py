# Copyright (C) 2021 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from datetime import datetime

import werkzeug

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class CustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "rma_order_count" in counters:
            values["rma_order_count"] = (
                request.env["rma.order"].search_count([])
                if request.env["rma.order"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
        return values

    @http.route(
        ["/my/rma/order", "/my/rma/order/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_orders_lines(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        RmaOrder = request.env["rma.order"]
        domain = []

        searchbar_sortings = {}

        sort_order = ""

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        # count for pager
        order_count = RmaOrder.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/rma/order",
            url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
            total=order_count,
            page=page,
            step=self._items_per_page,
        )
        # content according to pager
        orders = RmaOrder.search(
            domain, order=sort_order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_rma_line_history"] = orders.ids[:100]

        values.update(
            {
                "date": date_begin,
                "orders": orders.sudo(),
                "page_name": "rma_order",
                "pager": pager,
                "default_url": "/my/rma/order",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("rma_website.rma_order_portal", values)

    @http.route(
        [
            "/rma/order/<int:ticket_id>",
            "/rma/order/<int:ticket_id>/<access_token>",
            "/rma/order/<int:ticket_id>",
            "/rma/order/<int:ticket_id>/<access_token>",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def rma_order_view(self, ticket_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access(
                "rma.order", ticket_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        values = self._rma_order_get_page_view_values(order_sudo, access_token, **kw)

        return request.render("rma_website.rma_order_tmaplate_view", values)

    def _rma_order_get_page_view_values(self, order_sudo, access_token, **kwargs):
        values = {
            "page_name": "rma_order",
            "rma_order": order_sudo,
        }
        return self._get_page_view_values(
            order_sudo, access_token, values, "my_rma_line_history", False, **kwargs
        )

    @http.route("/rma/order/new", type="http", auth="public", website=True)
    def rma_counters(self, **kw):
        customer_ids = request.env["res.partner"].search([("customer_rank", ">", 0)])
        product_ids = request.env["product.product"].search([])
        lot_ids = request.env["stock.production.lot"].search([])
        operation_ids = request.env["rma.operation"].search([])
        operation_id = request.env.ref(
            "rma.rma_operation_customer_replace", raise_if_not_found=False
        )
        values = {
            "customer_ids": customer_ids,
            "product_ids": product_ids,
            "lot_ids": lot_ids,
            "operation_ids": operation_ids,
            "operation_id": operation_id,
        }
        return request.render("rma_website.rma_customer_portal", values)

    @http.route("/create/group", type="http", auth="public", website=True)
    def full_url_redirect(self, **post):
        order_obj = request.env["rma.order"]

        customer_id = post.get("customer", False)
        order_date = post.get("order_date", False)
        info = post.get("info", False)
        order_date = datetime.strptime(order_date, "%Y-%m-%dT%H:%M")

        products = post.get("products", False)
        lots = post.get("lots", False)
        references = post.get("references", False)
        operations = post.get("operations", False)
        return_qty = post.get("return_qty", False)
        price_units = post.get("price_units", False)
        line_ids = []
        vals = order_obj.default_get(
            ["in_warehouse_id", "company_id", "out_warehouse_id"]
        )
        if products and references and operations and return_qty and price_units:
            products = products.split(",")
            if lots:
                lots = lots.split(",")

            references = references.split(",")
            operations = operations.split(",")
            return_qty = return_qty.split(",")
            price_units = price_units.split(",")
            for i in range(0, len(operations)):
                product_id = request.env["product.product"].browse(int(products[i]))
                operation_id = request.env["rma.operation"].browse(int(operations[i]))
                warehouse_id = request.env["stock.warehouse"].browse(
                    int(vals.get("in_warehouse_id"))
                )

                location_id = operation_id.location_id.id or warehouse_id.lot_rma_id.id
                line_ids.append(
                    (
                        0,
                        0,
                        {
                            "partner_id": int(customer_id),
                            "product_id": products[i],
                            "uom_id": product_id.uom_id.id,
                            "lot_id": lots and lots[i],
                            "name": references[i],
                            "operation_id": operations[i],
                            "product_qty": return_qty[i],
                            "price_unit": price_units[i],
                            "in_route_id": operation_id.in_route_id.id,
                            "out_route_id": operation_id.out_route_id.id,
                            "in_warehouse_id": vals.get("in_warehouse_id"),
                            "out_warehouse_id": operation_id.out_warehouse_id.id,
                            "location_id": location_id,
                        },
                    )
                )

        vals.update(
            {
                "partner_id": int(customer_id),
                "date_rma": order_date,
                "comment": info,
                "rma_line_ids": line_ids,
                "assigned_to": False,
                "message_partner_ids": [(6, 0, [int(customer_id)])],
            }
        )
        order_obj.sudo().create(vals)
        return werkzeug.utils.redirect("/my/rma/order", 301)

    @http.route("/website/find/lot", type="json", auth="public", website=True)
    def website_find_lot(self, product_id, **post):
        return request.env["stock.production.lot"].search_read(
            [("product_id", "=", int(product_id))], ["name"]
        )
