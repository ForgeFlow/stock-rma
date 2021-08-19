odoo.define("rma_website.rma_website_portal", function (require) {
    "use strict";

    var time = require("web.time");

    var publicWidget = require("web.public.widget");
    const ajax = require("web.ajax");

    require("web.dom_ready");

    publicWidget.registry.RMAProduct = publicWidget.Widget.extend({
        selector: ".rma-table-input-tr",
        events: {
            "click .product-input": "product_input",
        },
        product_input: function (ev) {
            $(ev.currentTarget).parent().find(".lot").empty();
            if ($(ev.currentTarget).val()) {
                ajax.jsonRpc("/website/find/lot", "call", {
                    product_id: $(ev.currentTarget).val(),
                }).then((results) => {
                    $(ev.currentTarget).parent().parent().find(".lot option").remove();
                    _.each(results, (result) => {
                        $(ev.currentTarget)
                            .parent()
                            .parent()
                            .find(".lot")
                            .append(new Option(result.name, result.id));
                    });
                });
            }
        },
    });

    $(document).ready(function () {
        var datepickers_options = {
            minDate: moment({
                y: 1000,
            }),
            maxDate: moment({
                y: 9999,
                M: 11,
                d: 31,
            }),
            calendarWeeks: true,
            icons: {
                time: "fa fa-clock-o",
                date: "fa fa-calendar",
                next: "fa fa-chevron-right",
                previous: "fa fa-chevron-left",
                up: "fa fa-chevron-up",
                down: "fa fa-chevron-down",
            },
            locale: moment.locale(),
            format: time.getLangDatetimeFormat(),
        };
        $(".datetimepicker-input").datetimepicker(datepickers_options);
        const now = new Date();
        var year = now.getFullYear();
        var month =
            now.getMonth().toString().length === 1
                ? "0" + (now.getMonth() + 1).toString()
                : now.getMonth() + 1;
        var date =
            now.getDate().toString().length === 1
                ? "0" + now.getDate().toString()
                : now.getDate();
        var hours =
            now.getHours().toString().length === 1
                ? "0" + now.getHours().toString()
                : now.getHours();
        var minutes =
            now.getMinutes().toString().length === 1
                ? "0" + now.getMinutes().toString()
                : now.getMinutes();
        var seconds =
            now.getSeconds().toString().length === 1
                ? "0" + now.getSeconds().toString()
                : now.getSeconds();
        var formattedDateTime =
            year +
            "/" +
            month +
            "/" +
            date +
            "T" +
            hours +
            ":" +
            minutes +
            ":" +
            seconds;
        $(".datetimepicker-input").val(formattedDateTime);

        $(".btn-add-line").click(function (ev) {
            ev.preventDefault();

            var $add_line = $(this).parent().parent();
            var total_count = $("#hidden-total_counts").val() + 1;
            var $input_tr = $("tr.table-input-tr").clone();
            $input_tr.find(".product").attr("required", true);
            $input_tr.find(".product").attr("id", "product_" + total_count.toString());
            $input_tr.find(".reference").attr("required", true);
            $input_tr
                .find(".reference")
                .attr("id", "reference_" + total_count.toString());
            $input_tr.find(".operation").attr("required", true);
            $input_tr
                .find(".operation")
                .attr("id", "operation_" + total_count.toString());
            $input_tr.find(".return_qty").attr("required", true);
            $input_tr
                .find(".return_qty")
                .attr("id", "return_qty_" + total_count.toString());
            $input_tr.find(".price_unit").attr("required", true);
            $input_tr
                .find(".price_unit")
                .attr("id", "price_unit_" + total_count.toString());
            $("<tr>", {
                html: $input_tr.html(),
                class: "data-tr",
            }).insertBefore($add_line);
            $("#hidden-total_counts").val(total_count);
        });

        // Hide the lot dropdown options by default
        var $lot_select = $(this).parent().parent().find("#lot");
        $lot_select.children("option").hide();

        // Filter the lot dropdown options by product.
        $(document).on("change", ".product-input", function (ev) {
            ev.preventDefault();
            var $lot_select = $(this).parent().parent().find("#lot");
            $lot_select.children("option").hide();
            $lot_select.children("option[data-product^=" + $(this).val() + "]").show();
        });

        // To-Do: Improve the code to get the table data
        $("#a-submit-rma")
            .off("click")
            .click(function (ev) {
                ev.preventDefault();
                var $tbody = $(".form-table").find("tbody");
                var product_data = [];
                var lot_date = [];
                var reference_date = [];
                var operation_date = [];
                var return_qty_date = [];
                var price_unit_date = [];
                var is_required = [];
                $tbody.children().each(function (row, elem) {
                    if ($(elem).hasClass("data-tr")) {
                        if (!$(elem).find(".product").val()) {
                            is_required = true;
                            $(elem)
                                .find(".product")
                                .parent()
                                .find("p")
                                .removeClass("o_hidden");
                        } else {
                            $(elem)
                                .find(".product")
                                .parent()
                                .find("p")
                                .addClass("o_hidden");
                        }
                        if (!$(elem).find(".reference").val()) {
                            is_required = true;
                            $(elem)
                                .find(".reference")
                                .parent()
                                .find("p")
                                .removeClass("o_hidden");
                        } else {
                            $(elem)
                                .find(".reference")
                                .parent()
                                .find("p")
                                .addClass("o_hidden");
                        }
                        if (!$(elem).find(".operation").val()) {
                            is_required = true;
                            $(elem)
                                .find(".operation")
                                .parent()
                                .find("p")
                                .removeClass("o_hidden");
                        } else {
                            $(elem)
                                .find(".operation")
                                .parent()
                                .find("p")
                                .addClass("o_hidden");
                        }
                        if (!$(elem).find(".return_qty").val()) {
                            is_required = true;
                            $(elem)
                                .find(".return_qty")
                                .parent()
                                .find("p")
                                .removeClass("o_hidden");
                        } else {
                            $(elem)
                                .find(".return_qty")
                                .parent()
                                .find("p")
                                .addClass("o_hidden");
                        }
                        if (!$(elem).find(".return_qty").val()) {
                            is_required = true;
                            $(elem)
                                .find(".price_unit")
                                .parent()
                                .find("p")
                                .removeClass("o_hidden");
                        } else {
                            $(elem)
                                .find(".price_unit")
                                .parent()
                                .find("p")
                                .addClass("o_hidden");
                        }
                        product_data.push($(elem).find(".product").val());
                        lot_date.push($(elem).find(".lot").val());
                        reference_date.push($(elem).find(".reference").val());
                        operation_date.push($(elem).find(".operation").val());
                        return_qty_date.push($(elem).find(".return_qty").val());
                        price_unit_date.push($(elem).find(".price_unit").val());
                    }
                });
                if (is_required) {
                    $("#hidden-product").val(product_data.toString());
                    $("#hidden-lot").val(lot_date.toString());
                    $("#hidden-reference").val(reference_date.toString());
                    $("#hidden-operation").val(operation_date.toString());
                    $("#hidden-return_qty").val(return_qty_date.toString());
                    $("#hidden-price_unit").val(price_unit_date.toString());
                    $("#btn-submit").click();
                }
            });
    });
});
