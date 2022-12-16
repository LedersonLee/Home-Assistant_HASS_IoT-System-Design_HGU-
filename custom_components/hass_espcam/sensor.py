import json
from datetime import datetime
from pathlib import Path
from pprint import pformat

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import DEVICE_CLASS_ENERGY, ENERGY_KILO_WATT_HOUR, DEVICE_CLASS_MONETARY, \
    DEVICE_CLASS_TIMESTAMP
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.hass_espcam.const import LOGGER
from custom_components.hass_espcam.calculator import ElectricityCalculator

SENSOR_TYPES = {
    'electricity_consumption': ['사용량', ENERGY_KILO_WATT_HOUR, DEVICE_CLASS_ENERGY],
    'electricity_cost': ['예상 실시간 요금', '원', DEVICE_CLASS_MONETARY],
    'usage_compared_to_last_month': ['전월 대비 사용량', ENERGY_KILO_WATT_HOUR, DEVICE_CLASS_ENERGY],
    'date_time_updated': ['최근 업데이트', '', DEVICE_CLASS_TIMESTAMP],
}


def setup_platform(_, config, add_entities, discovery_info):
    # Add devices
    LOGGER.info(pformat(config))

    kwargs = {
        'snapshot_url': config.get('snapshot_url'),
        'roi_x': config.get('roi_x'),
        'roi_y': config.get('roi_y'),
        'roi_width': config.get('roi_width'),
        'roi_height': config.get('roi_height'),
        'debug': config.get('debug'),
        'decimals': config.get('decimals')
    }
    entities = []
    for sensor_type, attributes in SENSOR_TYPES.items():
        entities.append(
            ElectricityEntity(
                sensor_type, attributes[0], attributes[1], attributes[2], **kwargs
            )
        )

    add_entities(entities)


class ElectricityEntity(SensorEntity):
    _value_difference_margin = 30

    def __init__(self, sensor_type, name, unit, device_class, **kwargs) -> None:
        super().__init__()
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = None

        self.energy_object = ElectricityUsage()
        self.api = ElectricityCalculator()
        self._sensor_type = sensor_type
        self._value = 0
        self._values_accumulated = []
        self._extra_state_attributes = {}
        self.init_from_energy_object()

        try:
            self._kwargs = {
                'snapshot_url': kwargs['snapshot_url'],
                'roi': {
                    'x': kwargs.get('roi_x'),
                    'y': kwargs.get('roi_y'),
                    'width': kwargs.get('roi_width'),
                    'height': kwargs.get('roi_height')
                },
                'decimals': kwargs['decimals'],
                'debug': kwargs['debug']
            }
        except KeyError:
            LOGGER.error('Missing required configuration parameters')

    def init_from_energy_object(self):
        if self._sensor_type == 'electricity_consumption':
            self._value = self.energy_object.usage

        elif self._sensor_type == 'electricity_cost':
            self._value = 0

        elif self._sensor_type == 'date_time_updated':
            self._value = self.energy_object.last_updated

        elif self._sensor_type == 'usage_compared_to_last_month':
            self._value = self.energy_object.usage_last_month

    def get_session(self):
        return async_get_clientsession(self.hass)

    @property
    def state(self):
        return self._value

    async def async_update(self):
        if self._sensor_type == 'electricity_consumption':
            kwargs = {
                'session': self.get_session(),
                **self._kwargs
            }
            self._value = await self.api.update_value_recognized(**kwargs)

            if self._value:
                last_value = self._values_accumulated[-1] if self._values_accumulated else 0
                if last_value and abs(self._value - last_value) > self._value_difference_margin:
                    LOGGER.info(f'Value recognized seems wrong: {self._value}')
                    return

                self._values_accumulated.append(self._value)
                self._extra_state_attributes['values_accumulated'] = self._values_accumulated

            self._value = self._values_accumulated[-1] if self._values_accumulated else 0
            self.energy_object.usage = self._value

        elif self._sensor_type == 'date_time_updated':
            self._value = datetime.now()

        elif self._sensor_type == 'electricity_cost':
            usage = self.energy_object.usage - self.energy_object.usage_last_month

            if usage <= 200:
                base_cost = 910
                category = 1
            elif usage <= 400:
                base_cost = 1600
                category = 2
            else:
                base_cost = 7300
                category = 3

            if category == 1:
                cost_per_kwh = 88.3
                self._value = base_cost + (usage * cost_per_kwh)
            elif category == 2:
                cost_per_kwh = 182.9
                self._value = base_cost + (usage * cost_per_kwh)
            else:
                cost_per_kwh = 275.6
                self._value = base_cost + (usage * cost_per_kwh)

        else:
            self._value = self.energy_object.usage - self.energy_object.usage_last_month

        # Save to file every 30 minutes
        if datetime.now().minute % 30 == 0:
            self.energy_object.save_to_file()

            if datetime.now().day == 1:
                self.energy_object.set_usage()


class ElectricityUsage:
    path_json = Path('/home/homeassistant/.homeassistant/custom_components/hass_espcam/usage.json')

    def __init__(self):
        self.usage = None
        self.usage_last_month = None
        self.last_updated = datetime.now()
        self.load_saved()

    def load_saved(self):
        if self.path_json.is_file():
            with self.path_json.open(mode='r') as f:
                data = json.load(f)

            self.usage = data['usage']
            self.last_updated = datetime.strptime(data['last_updated'], '%Y-%m-%d %H:%M:%S')
            self.usage_last_month = data['usage_last_month']

    def save_to_file(self):
        with self.path_json.open(mode='w') as f:
            json.dump({
                'usage': self.usage,
                'last_updated': self.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
                'usage_last_month': self.usage_last_month
            }, f)

    def set_usage(self):
        self.usage_last_month = self.usage
