============================
Systemlogics Modula Scenario
============================

Imports::

    >>> import datetime
    >>> import os
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.systemlogics_modula.tests.tools \
    ...     import read_file
    >>> today = datetime.date.today()
    >>> yesterday = today - relativedelta(days=1)

Install stock Module::

    >>> config = activate_modules('systemlogics_modula')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create customer::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> category = ProductCategory(name='Category')
    >>> category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'Product'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('20')
    >>> template.save()
    >>> product, = template.products
    >>> product.code = 'P1'
    >>> product.cost_price = Decimal('8')
    >>> product.code = 'P1'
    >>> product.save()

    >>> product2 = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'Product'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('20')
    >>> template.save()
    >>> product2, = template.products
    >>> product2.cost_price = Decimal('8')
    >>> product2.code = 'P2'
    >>> product2.save()

Get stock locations::

    >>> Location = Model.get('stock.location')
    >>> warehouse_loc, = Location.find([('code', '=', 'WH')])
    >>> supplier_loc, = Location.find([('code', '=', 'SUP')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])
    >>> output_loc, = Location.find([('code', '=', 'OUT')])
    >>> input_loc, = Location.find([('code', '=', 'IN')])
    >>> storage_loc, = Location.find([('code', '=', 'STO')])

Create new modula location::

    >>> w1_loc = Location()
    >>> w1_loc.name = 'W1'
    >>> w1_loc.code = 'W1'
    >>> w1_loc.type = 'storage'
    >>> w1_loc.parent = storage_loc
    >>> w1_loc.save()

    >>> modula_loc = Location()
    >>> modula_loc.name = 'Modula'
    >>> modula_loc.code = 'MOD'
    >>> modula_loc.type = 'storage'
    >>> modula_loc.parent = w1_loc
    >>> modula_loc.systemlogics_modula = True
    >>> modula_loc.save()

Create SystemLogics Configuration::

    >>> SystemLogicsModula = Model.get('systemlogics.modula')

    >>> sm_imp_ordini = SystemLogicsModula()
    >>> sm_imp_ordini.name = 'IMP_ORDINI'
    >>> sm_imp_ordini.dbhost = 'xml'
    >>> sm_imp_ordini.dwarehouse = warehouse_loc
    >>> sm_imp_ordini.dpath = '/tmp'
    >>> sm_imp_ordini.save()

    >>> sm_exp_ordini = SystemLogicsModula()
    >>> sm_exp_ordini.name = 'EXP_ORDINI'
    >>> sm_exp_ordini.dbhost = 'xml'
    >>> sm_exp_ordini.warehouse = warehouse_loc
    >>> sm_exp_ordini.path = '/tmp'
    >>> sm_exp_ordini.save()

    >>> sm_imp_articoli = SystemLogicsModula()
    >>> sm_imp_articoli.name = 'IMP_ARTICOLI'
    >>> sm_imp_articoli.dbhost = 'xml'
    >>> sm_imp_articoli.warehouse = warehouse_loc
    >>> sm_imp_articoli.path = '/tmp'
    >>> sm_imp_articoli.save()

Create inventory::

    >>> StockMove = Model.get('stock.move')
    >>> incoming_move = StockMove()
    >>> incoming_move.product = product
    >>> incoming_move.uom = unit
    >>> incoming_move.quantity = 10
    >>> incoming_move.from_location = supplier_loc
    >>> incoming_move.to_location = storage_loc
    >>> incoming_move.planned_date = today
    >>> incoming_move.effective_date = today
    >>> incoming_move.company = company
    >>> incoming_move.unit_price = Decimal('1')
    >>> incoming_move.currency = company.currency
    >>> incoming_move.click('do')

    >>> incoming_move = StockMove()
    >>> incoming_move.product = product2
    >>> incoming_move.uom = unit
    >>> incoming_move.quantity = 10
    >>> incoming_move.from_location = supplier_loc
    >>> incoming_move.to_location = modula_loc
    >>> incoming_move.planned_date = today
    >>> incoming_move.effective_date = today
    >>> incoming_move.company = company
    >>> incoming_move.unit_price = Decimal('1')
    >>> incoming_move.currency = company.currency
    >>> incoming_move.click('do')

Create Shipment Out::

    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> shipment_out = ShipmentOut()
    >>> shipment_out.planned_date = today
    >>> shipment_out.customer = customer
    >>> shipment_out.warehouse = warehouse_loc
    >>> shipment_out.company = company
    >>> shipment_out.outgoing_moves.extend([StockMove()])
    >>> for move in shipment_out.outgoing_moves:
    ...     move.product = product
    ...     move.uom = unit
    ...     move.quantity = 1
    ...     move.from_location = output_loc
    ...     move.to_location = customer_loc
    ...     move.company = company
    ...     move.unit_price = Decimal('1')
    ...     move.currency = company.currency
    >>> shipment_out.save()
    >>> shipment_out.click('wait')
    >>> shipment_out.click('assign_try')
    True
    >>> shipment_out.systemlogics_modula == False
    True

    >>> shipment_out2 = ShipmentOut()
    >>> shipment_out2.planned_date = today
    >>> shipment_out2.customer = customer
    >>> shipment_out2.warehouse = warehouse_loc
    >>> shipment_out2.company = company
    >>> shipment_out2.outgoing_moves.extend([StockMove()])
    >>> for move in shipment_out2.outgoing_moves:
    ...     move.product = product2
    ...     move.uom = unit
    ...     move.quantity = 1
    ...     move.from_location = output_loc
    ...     move.to_location = customer_loc
    ...     move.company = company
    ...     move.unit_price = Decimal('1')
    ...     move.currency = company.currency
    >>> shipment_out2.save()
    >>> shipment_out2.click('wait')
    >>> inventory_move, = shipment_out2.inventory_moves
    >>> inventory_move.from_location = modula_loc
    >>> inventory_move.save()
    >>> shipment_out2.reload()
    >>> shipment_out2.click('assign_try')
    True
    >>> shipment_out2.systemlogics_modula == True
    True

    >>> shipment_out3 = ShipmentOut()
    >>> shipment_out3.planned_date = today
    >>> shipment_out3.customer = customer
    >>> shipment_out3.warehouse = warehouse_loc
    >>> shipment_out3.company = company

    >>> move = StockMove()
    >>> shipment_out3.outgoing_moves.append(move)
    >>> move.product = product
    >>> move.uom = unit
    >>> move.quantity = 1
    >>> move.from_location = output_loc
    >>> move.to_location = customer_loc
    >>> move.company = company
    >>> move.unit_price = Decimal('1')
    >>> move.currency = company.currency

    >>> move = StockMove()
    >>> shipment_out3.outgoing_moves.append(move)
    >>> move.product = product2
    >>> move.uom = unit
    >>> move.quantity = 1
    >>> move.from_location = output_loc
    >>> move.to_location = customer_loc
    >>> move.company = company
    >>> move.unit_price = Decimal('1')
    >>> move.currency = company.currency

    >>> shipment_out3.save()
    >>> shipment_out3.click('wait')
    >>> shipment_out3.click('assign_try')
    True
    >>> shipment_out3.systemlogics_modula == True
    True

Create Shipment Out Return::

    >>> ShipmentOutReturn = Model.get('stock.shipment.out.return')
    >>> shipment_out_return = ShipmentOutReturn()
    >>> shipment_out_return.planned_date = today
    >>> shipment_out_return.customer = customer
    >>> shipment_out_return.warehouse = warehouse_loc
    >>> shipment_out_return.company = company
    >>> shipment_out_return.incoming_moves.extend([StockMove()])
    >>> for move in shipment_out_return.incoming_moves:
    ...     move.product = product2
    ...     move.uom = unit
    ...     move.quantity = 1
    ...     move.from_location = customer_loc
    ...     move.to_location = input_loc
    ...     move.company = company
    ...     move.unit_price = Decimal('1')
    ...     move.currency = company.currency
    >>> shipment_out_return.save()
    >>> shipment_out_return.click('receive')
    >>> inventory_move, = shipment_out_return.inventory_moves
    >>> inventory_move.to_location = modula_loc
    >>> inventory_move.save()
    >>> shipment_out_return.click('do_systemlogics_modula')
    >>> shipment_out_return.reload()
    >>> shipment_out_return.systemlogics_modula == True
    True

Create Shipment In::

    >>> ShipmentIn = Model.get('stock.shipment.in')
    >>> shipment_in = ShipmentIn()
    >>> shipment_in.planned_date = today
    >>> shipment_in.supplier = supplier
    >>> shipment_in.warehouse = warehouse_loc
    >>> shipment_in.company = company
    >>> shipment_in.incoming_moves.extend([StockMove()])
    >>> for move in shipment_in.incoming_moves:
    ...     move.product = product2
    ...     move.uom = unit
    ...     move.quantity = 1
    ...     move.from_location = supplier_loc
    ...     move.to_location = input_loc
    ...     move.company = company
    ...     move.unit_price = Decimal('1')
    ...     move.currency = company.currency
    >>> shipment_in.save()
    >>> shipment_in.click('receive')
    >>> inventory_move, = shipment_in.inventory_moves
    >>> inventory_move.to_location = modula_loc
    >>> inventory_move.save()
    >>> shipment_in.click('do_systemlogics_modula')
    >>> shipment_in.reload()
    >>> shipment_in.systemlogics_modula == True
    True

Create Shipment Internal::

    >>> ShipmentInternal = Model.get('stock.shipment.internal')
    >>> shipment_internal = ShipmentInternal()
    >>> shipment_internal.planned_date = today
    >>> shipment_internal.from_location = storage_loc
    >>> shipment_internal.to_location = modula_loc
    >>> move = shipment_internal.moves.new()
    >>> move.product = product
    >>> move.quantity = 1
    >>> move.from_location = storage_loc
    >>> move.to_location = modula_loc
    >>> move.currency = company.currency
    >>> shipment_internal.click('wait')
    >>> shipment_internal.click('assign_try')
    True
    >>> shipment_internal.reload()
    >>> shipment_internal.systemlogics_modula == True
    True

Import EXP Ordini::

    >>> EXPOrdiniFile = Model.get('systemlogics.modula.exp.ordini.file')
    >>> ordine_file = os.path.join(os.path.dirname(__file__), 'exp_ordini.xml')
    >>> exp_ordini_file = EXPOrdiniFile()
    >>> exp_ordini_file.name = 'EXP_ORDINI1.XML'
    >>> exp_ordini_file.modula = sm_exp_ordini
    >>> exp_ordini_file.content = read_file(ordine_file).decode('utf-8')
    >>> exp_ordini_file.save()
    >>> exp_ordini_file.click('process')
    >>> exp_ordini_file.state == 'done'
    True
    >>> shipment_out2.reload()
    >>> shipment_out2.state == 'packed'
    True

    >>> ordine_file = os.path.join(os.path.dirname(__file__), 'exp_ordini_incomplete.xml')
    >>> exp_ordini_file = EXPOrdiniFile()
    >>> exp_ordini_file.name = 'EXP_ORDINI2.XML'
    >>> exp_ordini_file.modula = sm_exp_ordini
    >>> exp_ordini_file.content = read_file(ordine_file).decode('utf-8')
    >>> exp_ordini_file.save()
    >>> exp_ordini_file.click('process')
    >>> exp_ordini_file.state == 'done'
    True
    >>> shipment_out3.reload()
    >>> shipment_out3.state == 'assigned'
    True
    >>> m1, m2 = shipment_out3.inventory_moves
    >>> m1.state == 'assigned'
    True
    >>> m2.state == 'done'
    True
