#This file is part systemlogics_modula module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import Pool
from .systemlogics import *
from .location import *
from .product import *
from .stock import *

def register():
    Pool.register(
        SystemLogicsModula,
        Location,
        Product,
        ProductCode,
        ShipmentOut,
        ShipmentInternal,
        module='systemlogics_modula', type_='model')