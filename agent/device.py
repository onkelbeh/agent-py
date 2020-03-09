"""Classes that allow interacting with specific Agent devices."""

import logging
from enum import Enum
from typing import Optional
from urllib.parse import urlencode

_LOGGER = logging.getLogger(__name__)


class TimePeriod(Enum):
	"""Represents a period of time to check for events."""

	@property
	def period(self) -> str:
		"""Get the period of time."""
		# pylint: disable=unsubscriptable-object
		return self.value[0]

	@property
	def title(self) -> str:
		"""Explains what is measured in this period."""
		# pylint: disable=unsubscriptable-object
		return self.value[1]

	@staticmethod
	def get_time_period(value):
		"""Get the corresponding TimePeriod from the value.

		Example values: 'all', 'hour', 'day', 'week', or 'month'.
		"""
		for time_period in TimePeriod:
			if time_period.period == value:
				return time_period
		raise ValueError('{} is not a valid TimePeriod'.format(value))

	ALL = ('all', 'Events')
	HOUR = ('hour', 'Events Last Hour')
	DAY = ('day', 'Events Last Day')
	WEEK = ('week', 'Events Last Week')
	MONTH = ('month', 'Events Last Month')


class Device:
	"""Represents a device from Agent."""

	def __init__(self, client, raw_result):
		"""Create a new device."""
		self._client = client
		self._raw_result = raw_result
		self._oid = int(raw_result['id'])
		self._ot = int(raw_result['typeID'])

	@property
	def id(self) -> int:
		"""Get the Agent id number of this device."""
		# pylint: disable=invalid-name
		return self._oid

	@property
	def typeID(self) -> int:
		"""Get the Agent id number of this device."""
		# pylint: disable=invalid-name
		return self._ot

	@property
	def client(self) -> int:
		"""Get the Agent server client of this device."""
		# pylint: disable=invalid-name
		return self._client

	@property
	def name(self) -> str:
		"""Get the name of this device."""
		return self._raw_result['name']


	def update(self):
		"""Update the device from the Agent server."""
		self._raw_result = self._client.get_state('command.cgi?cmd=getObject&oid={0}&ot={1}'.format(self._oid,self._ot))

	@property
	def mjpeg_image_url(self) -> str:
		"""Get the mjpeg url of this device."""
		return 'video.mjpg?oid={0}'.format(self._oid)
	
	@property
	def mp4_url(self) -> str:
		"""Get the mp4 video url of this device."""
		return 'video.mp4?oid={0}'.format(self._oid)
	
	@property
	def webm_url(self) -> str:
		"""Get the mp4 video url of this device."""
		return 'video.webm?oid={0}'.format(self._oid)

	@property
	def still_image_url(self) -> str:
		"""Get the still jpeg image url of this device."""
		return 'grab.jpg?oid={0}'.format(self._oid)

	@property
	def recording(self) -> Optional[bool]:
		"""Indicate if this device is currently recording."""
		return self._raw_result['data']['recording']
	
	@property
	def alerted(self) -> Optional[bool]:
		"""Indicate if this device has alerted."""
		return self._raw_result['data']['alerted']

	@property
	def online(self) -> Optional[bool]:
		"""Indicate if this device is currently online."""
		return self._raw_result['data']['online']

	@property
	def alerts_active(self) -> Optional[bool]:
		"""Indicate if this device has alerts enabled."""
		return self._raw_result['data']['alertsActive']

	@property
	def connected(self) -> bool:
		"""Indicate if this device is currently connected."""
		return self._raw_result['data']['connected']

	@property
	def has_ptz(self) -> bool:
		"""Indicate if this device has PTZ capability."""
		return self._ot == 2 and self._raw_result['data']['ptzid'] != -1

	@property
	def raw_result(self) -> dict:
		return self._raw_result


	def enable(self):
		self._client.get_state('command.cgi?cmd=switchOn&oid={0}&ot={1}'.format(self._oid, self._ot))
		self._raw_result['data']['online'] = True


	def disable(self):
		self._client.get_state('command.cgi?cmd=switchOff&oid={0}&ot={1}'.format(self._oid, self._ot))
		self._raw_result['data']['online'] = False


	def record(self):
		self._client.get_state('command.cgi?cmd=record&oid={0}&ot={1}'.format(self._oid, self._ot))
		self._raw_result['data']['recording'] = True


	def record_stop(self):
		self._client.get_state('command.cgi?cmd=recordStop&oid={0}&ot={1}'.format(self._oid, self._ot))
		self._raw_result['data']['recording'] = False


	def alerts_on(self):
		self._client.get_state('command.cgi?cmd=alertsOn&oid={0}&ot={1}'.format(self._oid, self._ot))
		self._raw_result['data']['alertsActive'] = True


	def alerts_off(self):
		self._client.get_state('command.cgi?cmd=alertsOff&oid={0}&ot={1}'.format(self._oid, self._ot))
		self._raw_result['data']['alertsActive'] = False


	def get_events(self, time_period) -> Optional[int]:
		"""Get the number of events that have occurred on this device.

		Specifically only gets events that have occurred within the TimePeriod
		provided.
		"""
		date_filter = 3600*24*365*20
		if time_period == TimePeriod.HOUR:
			date_filter = 3600
		
		if time_period == TimePeriod.DAY:
			date_filter = 3600*24
		
		if time_period == TimePeriod.WEEK:
			date_filter = 3600*24*7
		
		if time_period == TimePeriod.MONTH:
			date_filter = 3600*24*30
		
		count_response = self._client.get_state(
			'eventcounts.json?oid={0}&ot={1}&secs={2}'.format(self._oid, self._ot, date_filter)
		)
		return count_response['count']
