.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

==========
RMA Kanban
==========

Currently RMA just provides a status for Draft/open/paid status which is not
enough to follow the full administrative process.

This administrative process can be sometimes quite complex with workflow that
might be different by customers.

Some are usual stages:

* RMA receiving
* RMA quoting
* RMA refunding
* RMA repairing
* Any custom stage

Configuration
=============
Stage are set up in the Settings Menu of Odoo application (after switching to
Developer Mode):

#. go to Settings > Technical > Kanban > Stages.
#. Create a new stage

Usage
=====
#. Go to Invoicing menu --> Customers --> Customer rmas
#. Enjoy the new kanban view
#. Drag and drop the rmas from stage to stage
#. In the form view, click on any new stage to change it

Roadmap / Known Issues
======================

* rma stages and status are currently not synchronized: this is so since
  every organization might have different needs and stages. Nevertheless, they
  can be easily sync'ed (at least from status to Stages) via server actions.


Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
