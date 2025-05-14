import logging

from . import GaroStatus
from .const import Mode, Connector

HYSTERESIS = 0.1
COOLDOWN_MINUTES = 2
P1 = 0
P3 = 1
DEFAULT_POWER = {
    0: (3.7, 10.7),
    6: (1.4, 2.8),
    7: (1.6, 3.1),
    8: (1.8, 5.1),
    9: (2.1, 5.7),
    10: (2.3, 6.6),
    11: (2.5, 7.2),
    12: (2.8, 7.9),
    13: (3.0, 8.6),
    14: (3.2, 9.4),
    15: (3.4, 10.1),
    16: (3.7, 10.7),
}

_LOGGER = logging.getLogger(__name__)

class GaroLimiter:

    def __init__(self, limit: bool, energy_limit: float ):
        self._limit = limit
        self._energy_limit = energy_limit
        self._selected_mode = None
        self._mode = None
        self._current_limit = 0
        self._n_phases = P1
        self._power = 0.0
        self._prediction = 0.0
        self._minute = 0
        self._mode_change_minute = None

    @property
    def limit(self) -> bool:
        return self._limit

    def is_initialized(self) -> bool:
        return self._mode and self._current_limit and self._prediction

    def get_mode_from_limit(self, limit: bool) -> Mode | None:
        self._limit = limit
        return self._get_mode_according_to_limit() if self._limit else None

    def get_mode_from_energy_limit(self, energy_limit: float) -> Mode | None:
        self._energy_limit = energy_limit
        return self._get_mode_according_to_limit() if self._limit else None

    def get_mode_from_selected_mode(self, selected_mode: Mode) -> Mode | None:
        self._selected_mode = selected_mode
        return selected_mode if selected_mode is Mode.OFF or not self._limit else self._get_mode_according_to_limit()

    def get_mode_from_status(self, status: GaroStatus) -> Mode | None:
        self._mode = status.mode
        self._current_limit = status.current_limit
        self._power = status.current_charging_power / 1000
        if status.connector in (Connector.NOT_CONNECTED, Connector.SEARCH_COMM):
            self._n_phases = P1            # reset number of phases at car unplug
        elif status.number_of_phases == 3: # ignore number of phase going from 3 to 1 (happens when charging stops)
            self._n_phases = P3
        if self._selected_mode is None:
            self._selected_mode = status.mode
        return self._get_mode_according_to_limit() if self._limit else None

    def get_mode_from_prediction_and_minute(self, prediction: float, minute: int) -> Mode | None:
        prediction = round(prediction, 2)
        if self._prediction != prediction or self._minute != minute:
            self._prediction = prediction
            self._minute = minute
            if self._mode_change_minute is not None and (self._minute - self._mode_change_minute) % 60 >= COOLDOWN_MINUTES:
                self._mode_change_minute = None
            if self._limit:
                return self._get_mode_according_to_limit()
        return None


    def _get_mode_according_to_limit(self) -> Mode | None:
        mode = None
        if self._prediction > self._energy_limit and self._mode in (Mode.ON, Mode.SCHEMA):
            # turn off because of prediction is at limit or above
            mode = Mode.OFF
        elif self._mode is Mode.OFF and self._selected_mode in (Mode.ON, Mode.SCHEMA):
            # turn on/to schema if charger consumption + prediction is below limit
            charger_power = self._power or DEFAULT_POWER[self._current_limit][self._n_phases]
            charger_estimate = charger_power * (60 - self._minute) / 60
            condition = round(self._prediction + charger_estimate + HYSTERESIS, 2)
            _LOGGER.debug(f"Prediction if charging plus hysteresis {condition} from power {charger_power}")
            if condition < self._energy_limit:
                mode = self._selected_mode
        elif self._mode != self._selected_mode:
            # nothing to do from prediction/limit, set mode to selected mode
            mode = self._selected_mode
        _LOGGER.debug(f"Mode is {self._mode}, new according to limiter: {mode}, {self.__dict__}")
        if mode:
            if self._mode_change_minute is None:
                self._mode_change_minute = self._minute
                return mode
            _LOGGER.debug(f"Cooldown until {(self._mode_change_minute + COOLDOWN_MINUTES) % 60}")
        return None
