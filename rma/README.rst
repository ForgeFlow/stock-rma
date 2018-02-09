.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
    :alt: License LGPL-3

======================================
RMA (Return Merchandise Authorization)
======================================

A Return Merchandise Authorization (RMA), is a part of the process of
returning a product in order to receive a refund, replacement, or repair
during the product's warranty period.

The purchaser of the product must contact the manufacturer (or distributor
or retailer) to obtain authorization to return the product.

The resulting RMA number must be displayed on or included in the returned
product's packaging.

The issuance of an RMA is a key gatekeeping moment in the reverse logistics
cycle, providing the vendor with a final opportunity to diagnose and correct
the customer's problem with the product (such as improper installation or
configuration) before the customer permanently relinquishes ownership
of the product to the manufacturer, commonly referred to as a return.

As returns are costly for the vendor and inconvenient for the customer,
any return that can be prevented benefits both parties.


Configuration
=============

Security
--------

Go to Settings > Users and assign the appropiate permissions to users.
Different security groups grant distinct levels of access to the RMA features.

* Users in group "RMA Customer User" or "RMA Supplier User" can access to,
  create and process RMA's associated to customers or suppliers respectively.

* Users in group "RMA Manager" can access to, create, approve and process RMA's
  associated to both customers and suppliers.

RMA Approval Policy
-------------------

There are two RMA approval policies in product catogories:

* One step: Always auto-approve RMAs that only contain products within
  categories with this policy.
* Two steps: A RMA order containing a product within a category with this
  policy will request the RMA manager approval.

In order to change the approval policy of a product category follow the next
steps:

#. Go to *Inventory > Configuration > Products > Product Categories*.
#. Select one and change the field *RMA Approval Policy* to your convenience.

Other Settings
--------------

#. Go to Inventory > Configuration > Settings > Return Merchandising
   Authorization and select the option "Display 3 fields on rma: partner,
   invoice address, delivery address" if needed.
#. Go to Inventory > Configuration > Warehouse management > Warehouses and add
   a default RMA location and RMA picking type for customers and suppliers RMA
   picking type. In case the warehouse is configured to use routes, you need to
   create at least one route per rma type with at least two push rules (one for
   inbound another for outbound) it's very important to select the type of
   operation supplier if we are moving in the company and customer if we are
   moving out of the company.

Usage
=====

RMA are accessible though Inventory menu. There's four menus, divided by type.
Users can access to the list of RMA or RMA lines.

Create an RMA:

#. Select a partner. Enter RMA lines associated to an existing picking, or
   manually.
#. Request approval and approve.
#. Click on RMA Lines button.
#. Click on more and select an option: "Receive products", "Create Delivery
   Order".
#. Go back to the RMA. Set the RMA to done if not further action is required.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/Eficent/stock-rma/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Jordi Ballester Alomar <jordi.ballester@eficent.com>
* Aaron Henriquez <ahenriquez@eficent.com>
* Lois Rilo <lois.rilo@eficent.com>
* Bhavesh Odedra <bodedra@opensourceintegrators.com>

Maintainer
----------

This module is maintained by Eficent.
