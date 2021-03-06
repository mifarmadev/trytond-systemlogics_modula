#This file is part systemlogics_modula module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import  ModelView, fields
from trytond.transaction import Transaction
from trytond.pyson import Eval
from trytond.wizard import Wizard, StateView, Button, StateTransition
from trytond.tools import grouped_slice
import logging

__all__ = ['ShipmentIn', 'ShipmentOut', 'ShipmentOutReturn', 'ShipmentInternal',
    'ShipmentOutSystemlogicsModulaExportStart', 'ShipmentOutSystemlogicsModulaExport',
    'ShipmentOutSystemlogicsModulaCheckStart', 'ShipmentOutSystemlogicsModulaCheck']

logger = logging.getLogger(__name__)


class ShipmentIn(metaclass=PoolMeta):
    __name__ = 'stock.shipment.in'
    systemlogics_modula = fields.Boolean('SystemLogics Modula')

    @classmethod
    def __setup__(cls):
        super(ShipmentIn, cls).__setup__()
        cls._buttons.update({
            'do_systemlogics_modula': {
                'invisible': Eval('state').in_(['draft', 'cancel']),
                },
            })

    @staticmethod
    def default_systemlogics_modula():
        return False

    @classmethod
    def copy(cls, shipments, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['systemlogics_modula'] = None
        return super(ShipmentIn, cls).copy(shipments, default=default)

    @classmethod
    def generate_systemlogics_modula(cls, shipments):
        '''Active System Logics process when a move location is systemlogics marked'''
        SystemLogicsModula = Pool().get('systemlogics.modula')

        deposit_shipments = []
        for s in shipments:
            systemLogics = False
            for move in s.inventory_moves:
                if move.to_location.systemlogics_modula:
                    systemLogics = True

            if systemLogics:
                deposit_shipments.append(s)

        if deposit_shipments:
            cls.write(deposit_shipments, {'systemlogics_modula': True})

            # Force not get a rollback to generate XML file
            shipment_ids = [s.id for s in deposit_shipments]
            Transaction().commit()
            # Search shipment ID to sure not have a rollback
            shipments = cls.search([
                ('id', 'in', shipment_ids),
                ])
            SystemLogicsModula.imp_ordini(
                shipments, template='IMP_ORDINI_IN', type_='V')

    @classmethod
    @ModelView.button
    def do_systemlogics_modula(cls, shipments):
        cls.generate_systemlogics_modula(shipments)


class ShipmentOut(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'
    systemlogics_modula = fields.Boolean('SystemLogics Modula')
    systemlogics_modula_completed = fields.Boolean(
        'SystemLogics Modula Completed')
    systemlogics_modula_sended = fields.Boolean('SystemLogics Modula Sended')
    ship_create_date = fields.Function(fields.DateTime('Create Date'),
        'get_ship_create_date')

    @staticmethod
    def default_systemlogics_modula():
        return False

    @staticmethod
    def default_systemlogics_modula_completed():
        return False

    @staticmethod
    def default_systemlogics_modula_sended():
        return False

    def get_ship_create_date(self, name):
        return self.create_date

    @classmethod
    def copy(cls, shipments, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['systemlogics_modula'] = False
        default['systemlogics_modula_completed'] = False
        default['systemlogics_modula_sended'] = False
        return super(ShipmentOut, cls).copy(shipments, default=default)

    @classmethod
    def generate_systemlogics_modula_file(cls, shipments):
        SystemLogicsModula = Pool().get('systemlogics.modula')

        # Force not get a rollback to generate XML file
        shipment_ids = [s.id for s in shipments]
        Transaction().commit()

        # Search shipment ID to sure not have a rollback
        shipments = cls.search([
            ('id', 'in', shipment_ids),
            ], order=[('systemlogics_modula_completed', 'DESC')])
        SystemLogicsModula.imp_ordini(
            shipments, template='IMP_ORDINI_OUT', type_='P')

    @classmethod
    def check_systemlogics_modula(cls, shipments):
        pool = Pool()
        Configuration = pool.get('stock.configuration')

        config = Configuration(1)
        if not (Transaction().context.get('generate_systemlogics_modula',
                config.try_generate_systemlogics_modula)):
            return

        to_write = []
        values = {
            'systemlogics_modula': True
            }
        for shipment in shipments:
            if hasattr(shipment, 'review'):
                if shipment.review:
                    continue
            systemLogics = False
            completed = True
            for move in shipment.inventory_moves:
                if move.from_location.systemlogics_modula:
                    systemLogics = True
                else:
                    completed = False
            if systemLogics:
                values = values.copy()
                if completed:
                    values['systemlogics_modula_completed'] = True
                else:
                    values['systemlogics_modula_completed'] = False
                to_write.extend(([shipment], values))
        if to_write:
            cls.write(*to_write)

    @classmethod
    def generate_systemlogics_modula(cls, shipments):
        '''Generate SystemLogics Modula'''
        Configuration = Pool().get('stock.configuration')

        config = Configuration(1)
        if not (Transaction().context.get('generate_systemlogics_modula',
                config.try_generate_systemlogics_modula)):
            return

        to_write = []
        shipments_modula = []
        value = {
            'systemlogics_modula_sended': True
            }
        for shipment in shipments:
            if hasattr(shipment, 'review'):
                if shipment.review:
                    continue
                shipments_modula.append(shipment)
                to_write.extend(([shipment], value))

        if shipments_modula:
            cls.write(*to_write)
            cls.generate_systemlogics_modula_file(shipments_modula)

    @classmethod
    def assign(cls, shipments):
        super(ShipmentOut, cls).assign(shipments)
        assigned = [s for s in shipments if s.state == 'assigned']
        cls.check_systemlogics_modula(assigned)
        cls.generate_systemlogics_modula(assigned)

    @classmethod
    def check_systemlogics_modula_scheduler(cls, args=None):
        '''
        This method is intended to be called from ir.cron
        args: warehouse ids [ids]
        '''
        pool = Pool()
        Configuration = pool.get('stock.configuration')
        config = Configuration(1)

        domain = [
            ('state', '=', 'assigned'),
            ('systemlogics_modula', '=', False),
            ]
        if args:
            domain.append(
                ('warehouse', 'in', args),
                )
        shipments = cls.search(domain)

        len_ships = len(shipments)
        logger.info(
            'Scheduler Try Check Systemlogics Modula. Total: %s' % (
                len_ships))
        if len_ships:
            blocs = 1
            slice_systemlogics_modula = (config.slice_systemlogics_modula or
                len_ships)
            with Transaction().set_context(generate_systemlogics_modula=True):
                for sub_shipments in grouped_slice(shipments,
                        slice_systemlogics_modula):
                    logger.info('Start bloc %s of %s.' % (
                            blocs, len_ships/slice_systemlogics_modula))
                    cls.check_systemlogics_modula(list(sub_shipments))
                    logger.info('End bloc %s.' % blocs)
                    blocs += 1
        logger.info('End Scheduler Try Check Systemlogics Modula.')

    @classmethod
    def generate_systemlogics_modula_scheduler(cls, args=None):
        '''
        This method is intended to be called from ir.cron
        args: warehouse ids [ids]
        '''
        pool = Pool()
        Configuration = pool.get('stock.configuration')
        config = Configuration(1)

        domain = [
            ('state', '=', 'assigned'),
            ('systemlogics_modula', '=', True),
            ('systemlogics_modula_sended', '=', False),
            ]
        if args:
            domain.append(
                ('warehouse', 'in', args),
                )
        shipments = cls.search(domain)

        len_ships = len(shipments)
        logger.info(
            'Scheduler Try generate Systemlogics Modula. Total: %s' % (
                len_ships))
        if len_ships:
            blocs = 1
            slice_systemlogics_modula = (config.slice_systemlogics_modula or
                len_ships)
            with Transaction().set_context(generate_systemlogics_modula=True):
                for sub_shipments in grouped_slice(shipments,
                        slice_systemlogics_modula):
                    logger.info('Start bloc %s of %s.' % (
                            blocs, len_ships/slice_systemlogics_modula))
                    cls.generate_systemlogics_modula(list(sub_shipments))
                    logger.info('End bloc %s.' % blocs)
                    blocs += 1
        logger.info('End Scheduler Try generate Systemlogics Modula.')


class ShipmentOutReturn(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out.return'
    systemlogics_modula = fields.Boolean('SystemLogics Modula')

    @classmethod
    def __setup__(cls):
        super(ShipmentOutReturn, cls).__setup__()
        cls._buttons.update({
            'do_systemlogics_modula': {
                'invisible': Eval('state').in_(['draft', 'cancel']),
                },
            })

    @staticmethod
    def default_systemlogics_modula():
        return False

    @classmethod
    def copy(cls, shipments, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['systemlogics_modula'] = None
        return super(ShipmentOutReturn, cls).copy(shipments, default=default)

    @classmethod
    def generate_systemlogics_modula(cls, shipments):
        '''Active System Logics process when a move location is systemlogics marked'''
        SystemLogicsModula = Pool().get('systemlogics.modula')

        deposit_shipments = []
        for s in shipments:
            systemLogics = False
            for move in s.inventory_moves:
                if move.to_location.systemlogics_modula:
                    systemLogics = True

            if systemLogics:
                deposit_shipments.append(s)

        if deposit_shipments:
            cls.write(deposit_shipments, {'systemlogics_modula': True})

            # Force not get a rollback to generate XML file
            shipment_ids = [s.id for s in deposit_shipments]
            Transaction().commit()
            # Search shipment ID to sure not have a rollback
            shipments = cls.search([
                ('id', 'in', shipment_ids),
                ])
            SystemLogicsModula.imp_ordini(
                shipments, template='IMP_ORDINI_IN', type_='V')

    @classmethod
    @ModelView.button
    def do_systemlogics_modula(cls, shipments):
        cls.generate_systemlogics_modula(shipments)


class ShipmentInternal(metaclass=PoolMeta):
    __name__ = 'stock.shipment.internal'
    systemlogics_modula = fields.Boolean('SystemLogics Modula')

    @staticmethod
    def default_systemlogics_modula():
        return False

    @classmethod
    def copy(cls, shipments, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['systemlogics_modula'] = None
        return super(ShipmentInternal, cls).copy(shipments, default=default)

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

        if extract_shipments or deposit_shipments:
            cls.write(extract_shipments + deposit_shipments, {'systemlogics_modula': True})

            # Force not get a rollback to generate XML file
            extract_shipments_ids = [shipment.id for shipment in extract_shipments]
            deposit_shipments_ids = [shipment.id for shipment in deposit_shipments]
            Transaction().commit()

            if extract_shipments_ids:
                # Search shipment ID to sure not have a rollback
                ext_shipments = cls.search([
                    ('id', 'in', extract_shipments_ids),
                    ])
                SystemLogicsModula.imp_ordini(
                    ext_shipments, template='IMP_ORDINI_INTERNAL', type_='P')
            if deposit_shipments_ids:
                # Search shipment ID to sure not have a rollback
                dep_shipments = cls.search([
                    ('id', 'in', deposit_shipments_ids),
                    ])
                SystemLogicsModula.imp_ordini(
                    dep_shipments, template='IMP_ORDINI_INTERNAL', type_='V')

    @classmethod
    def assign(cls, shipments):
        super(ShipmentInternal, cls).assign(shipments)
        cls.generate_systemlogics_modula(shipments)


class ShipmentOutSystemlogicsModulaExportStart(ModelView):
    'Customer shipments export Systemlogics Modula Start'
    __name__ = 'stock.shipment.out.systemlogics.modula.export.start'
    shipments = fields.Many2Many('stock.shipment.out', None, None, 'Shipments',
        required=True, domain=[
            ('state', '=', 'assigned'),
            ('systemlogics_modula', '=', True),
            ('systemlogics_modula_sended', '=', False),
            ],
        help='Assigned customer shipments to export Systemlogics Modula.')

    @classmethod
    def default_shipments(cls):
        ShipmentOut = Pool().get('stock.shipment.out')

        active_ids = Transaction().context.get('active_ids', [])
        domain = []
        domain.extend(cls.shipments.domain)
        if active_ids:
            domain.append(
                ('id', 'in', active_ids)
                )
        shipments = ShipmentOut.search(domain)
        return [s.id for s in shipments]


class ShipmentOutSystemlogicsModulaExport(Wizard):
    'Customer shipments export Systemlogics Modula'
    __name__ = 'stock.shipment.out.systemlogics.modula.export'

    start = StateView('stock.shipment.out.systemlogics.modula.export.start',
        'systemlogics_modula.shipment_out_export_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Export', 'export', 'tryton-ok', True),
            ])
    export = StateTransition()

    def transition_export(self):
        ShipmentOut = Pool().get('stock.shipment.out')

        shipments = list(self.start.shipments)
        if shipments:
            with Transaction().set_context(generate_systemlogics_modula=True):
                ShipmentOut.generate_systemlogics_modula(shipments)
        return 'end'


class ShipmentOutSystemlogicsModulaCheckStart(ModelView):
    'Customer shipments check Systemlogics Modula Start'
    __name__ = 'stock.shipment.out.systemlogics.modula.check.start'
    shipments = fields.Many2Many('stock.shipment.out', None, None, 'Shipments',
        required=True, domain=[
            ('state', '=', 'assigned'),
            ],
        help='Assigned customer shipments to check Systemlogics Modula.')

    @staticmethod
    def default_shipments():
        ShipmentOut = Pool().get('stock.shipment.out')

        active_ids = Transaction().context.get('active_ids', [])
        domain = [
            ('state', '=', 'assigned'),
            ('systemlogics_modula', '=', False),
            ]
        if active_ids:
            domain.append(
                ('id', 'in', active_ids)
                )
        shipments = ShipmentOut.search(domain)
        return [s.id for s in shipments]


class ShipmentOutSystemlogicsModulaCheck(Wizard):
    'Customer shipments check Systemlogics Modula'
    __name__ = 'stock.shipment.out.systemlogics.modula.check'

    start = StateView('stock.shipment.out.systemlogics.modula.check.start',
        'systemlogics_modula.shipment_out_check_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Check', 'check', 'tryton-ok', True),
            ])
    check = StateTransition()

    def transition_check(self):
        ShipmentOut = Pool().get('stock.shipment.out')

        shipments = list(self.start.shipments)
        if shipments:
            with Transaction().set_context(generate_systemlogics_modula=True):
                ShipmentOut.check_systemlogics_modula(shipments)
        return 'end'
