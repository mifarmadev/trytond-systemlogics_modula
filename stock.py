#This file is part systemlogics_modula module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import fields

__all__ = ['ShipmentOut', 'ShipmentInternal']
__metaclass__ = PoolMeta


class ShipmentOut:
    __name__ = 'stock.shipment.out'
    systemlogics_modula = fields.Boolean('SystemLogics Modula')

    @staticmethod
    def default_systemlogics_modula():
        return False

    @classmethod
    def generate_systemlogics_modula(cls, shipments):
        '''Active System Logics process when a move from location is systemlogics marked'''
        SystemLogicsModula = Pool().get('systemlogics.modula')

        systemlogics_shipments = []
        for s in shipments:
            systemLogics = False
            for move in s.inventory_moves:
                if move.from_location.systemlogics_modula:
                    systemLogics = True
                    break
            if systemLogics:
                systemlogics_shipments.append(s)

        # mark shipment is in systemlogics process
        if systemlogics_shipments:
            cls.write(systemlogics_shipments, {'systemlogics_modula': True})
        SystemLogicsModula.imp_ordini(
            systemlogics_shipments, template='IMP_ORDINI_OUT', type_='P')

    @classmethod
    def assign(cls, shipments):
        super(ShipmentOut, cls).assign(shipments)
        cls.generate_systemlogics_modula(shipments)


class ShipmentInternal:
    __name__ = 'stock.shipment.internal'
    systemlogics_modula = fields.Boolean('SystemLogics Modula')

    @staticmethod
    def default_systemlogics_modula():
        return False

    @classmethod
    def generate_systemlogics_modula(cls, shipments):
        '''Active System Logics process when a move location is systemlogics marked'''
        SystemLogicsModula = Pool().get('systemlogics.modula')

        extract_shipments = []
        deposit_shipments = []
        for s in shipments:
            if s.from_location.systemlogics_modula:
                extract_shipments.append(s)
            if s.to_location.systemlogics_modula:
                deposit_shipments.append(s)

        # mark shipment is in systemlogics process
        if extract_shipments or deposit_shipments:
            cls.write(extract_shipments + deposit_shipments, {'systemlogics_modula': True})
        if extract_shipments:
            SystemLogicsModula.imp_ordini(
                extract_shipments, template='IMP_ORDINI_IN', type_='P')
        if deposit_shipments:
            SystemLogicsModula.imp_ordini(
                deposit_shipments, template='IMP_ORDINI_IN', type_='V')

    @classmethod
    def assign(cls, shipments):
        super(ShipmentInternal, cls).assign(shipments)
        cls.generate_systemlogics_modula(shipments)