import logging

from homeassistant.util.dt import now

from . import utils

_LOGGER = logging.getLogger(__name__)

class GaroMeter:
    def __init__(
            self,
            json = None,
            current_divider = 1,
            power_divider = 1):

        self._current_divider = current_divider
        self._power_divider = power_divider
        self._serial_number = ""
        self._type = 0
        self._l1_current = 0.0
        self._l2_current = 0.0
        self._l3_current = 0.0
        self._l1_power = 0.0
        self._l2_power = 0.0
        self._l3_power = 0.0
        self._apparent_power = 0.0
        self._accumulated_energy = 0.0
        self._minute = None
        self._accumulated_energy_at_start_of_hour = 0.0
        self._predicted_hour_consumption = 0.0
        self._has_changed = False
        self.load(json)

    def load(self, json = None) -> bool:
        self._has_changed = False
        if not json:
            return False
        self._has_changed = False

        self.serial_number = utils.read_value(json, 'meterSerial', self._serial_number)
        self.type = utils.read_value(json, 'type', self._type)
        self.l1_current = utils.read_value(json, 'phase1Current', self._l1_current)
        self.l2_current = utils.read_value(json, 'phase2Current', self._l2_current)
        self.l3_current = utils.read_value(json, 'phase3Current', self._l3_current)
        self.l1_power = utils.read_value(json, 'phase1InstPower', self._l1_power)
        self.l2_power = utils.read_value(json, 'phase2InstPower', self._l2_power)
        self.l3_power = utils.read_value(json, 'phase3InstPower', self._l3_power)
        self.apparent_power = utils.read_value(json, 'apparentPower', self._apparent_power)
        self.accumulated_energy = utils.read_value(json, 'accEnergy', self._accumulated_energy)

        # TODO, is it possible to get the value of accumulated_energy at minute 0 from history?
        minute = now().minute
        if self._minute is None:
            self.accumulated_energy_at_start_of_hour = self._accumulated_energy
            _LOGGER.debug(f"Initializing, minute is {minute} setting energy soh to {self._accumulated_energy_at_start_of_hour}")
        elif minute < self._minute:
            self.accumulated_energy_at_start_of_hour = self._accumulated_energy
            _LOGGER.debug(f"minute: {minute}, self.minute: {self._minute}, soh: {self._accumulated_energy_at_start_of_hour}")
        self.minute = minute

        return self._has_changed

    def calculate_predicted_hour_consumption(self, voltage: int | None) -> None:
        energy_so_far = self.accumulated_energy - self.accumulated_energy_at_start_of_hour
        if voltage is not None:
            power = (self.l1_current + self.l2_current + self.l3_current) / 1000 * voltage
        else:
            power = self.apparent_power
        self.predicted_hour_consumption = energy_so_far + power * (60 - self._minute or 0) / 60

    @property
    def has_changed(self):
        return self._has_changed
    
    @property
    def serial_number(self):
        return self._serial_number
    @serial_number.setter
    def serial_number(self, value):
        if self._serial_number == value:
            return
        self._serial_number = value
        self._has_changed = True

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        if self._type == value:
            return
        self._type = value
        self._has_changed = True

    @property
    def l1_current(self):
        return self._l1_current / self._current_divider
    @l1_current.setter
    def l1_current(self, value):
        if self._l1_current == value:
            return
        self._l1_current = value
        self._has_changed = True

    @property
    def l2_current(self):
        return self._l2_current / self._current_divider
    @l2_current.setter
    def l2_current(self, value):
        if self._l2_current == value:
            return
        self._l2_current = value
        self._has_changed = True

    @property
    def l3_current(self):
        return self._l3_current / self._current_divider
    @l3_current.setter
    def l3_current(self, value):
        if self._l3_current == value:
            return
        self._l3_current = value
        self._has_changed = True

    @property
    def l1_power(self):
        return self._l1_power / self._power_divider
    @l1_power.setter
    def l1_power(self, value):
        if self._l1_power == value:
            return
        self._l1_power = value
        self._has_changed = True

    @property
    def l2_power(self):
        return self._l2_power / self._power_divider
    @l2_power.setter
    def l2_power(self, value):
        if self._l2_power == value:
            return
        self._l2_power = value
        self._has_changed = True

    @property
    def l3_power(self):
        return self._l3_power / self._power_divider
    @l3_power.setter
    def l3_power(self, value):
        if self._l3_power == value:
            return
        self._l3_power = value
        self._has_changed = True

    @property
    def apparent_power(self):
        return self._apparent_power / self._power_divider
    @apparent_power.setter
    def apparent_power(self, value):
        if self._apparent_power == value:
            return
        self._apparent_power = value
        self._has_changed = True

    @property
    def accumulated_energy(self):
        return self._accumulated_energy / 1000
    @accumulated_energy.setter
    def accumulated_energy(self, value):
        if self._accumulated_energy == value:
            return
        self._accumulated_energy = value
        self._has_changed = True

    @property
    def minute(self):
        return self._minute
    @minute.setter
    def minute(self, value):
        if self._minute == value:
            return
        self._minute = value
        self._has_changed = True

    @property
    def accumulated_energy_at_start_of_hour(self):
        return self._accumulated_energy_at_start_of_hour / 1000
    @accumulated_energy_at_start_of_hour.setter
    def accumulated_energy_at_start_of_hour(self, value):
        if self._accumulated_energy_at_start_of_hour == value:
            return
        self._accumulated_energy_at_start_of_hour = value
        self._has_changed = True

    @property
    def predicted_hour_consumption(self):
        return self._predicted_hour_consumption
    @predicted_hour_consumption.setter
    def predicted_hour_consumption(self, value):
        if self.predicted_hour_consumption == value:
            return
        self._predicted_hour_consumption = value
        self._has_changed = True