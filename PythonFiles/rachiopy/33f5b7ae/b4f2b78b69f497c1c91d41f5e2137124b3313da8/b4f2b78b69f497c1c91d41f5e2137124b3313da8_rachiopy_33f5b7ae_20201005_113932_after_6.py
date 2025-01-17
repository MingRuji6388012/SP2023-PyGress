"""Device object test module"""

import unittest
import uuid
from unittest.mock import patch
from random import randrange

from rachiopy import Device
from tests.constants import BASE_API_URL, AUTHTOKEN, SUCCESS200HEADERS
from tests.constants import SUCCESS204HEADERS, JSONBODY


class TestDeviceMethods(unittest.TestCase):
    """Class containing the Device object test cases."""

    def setUp(self):
        self.device = Device(AUTHTOKEN)

    def test_init(self):
        """Test if the constructor works as expected."""
        self.assertEqual(self.device.authtoken, AUTHTOKEN)

    @patch("httplib2.Http.request")
    def test_get(self, mock):
        """Test if the get method works as expected."""
        mock.return_value = (SUCCESS200HEADERS, JSONBODY)

        deviceid = uuid.uuid4()

        self.device.get(deviceid)

        args, kwargs = mock.call_args

        # Check that the mock function is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/" f"{deviceid}",
        )
        self.assertEqual(args[1], "GET")
        self.assertEqual(kwargs["body"], None)

    @patch("httplib2.Http.request")
    def test_current_schedule(self, mock):
        """Test if the current schedule method works as expected."""
        mock.return_value = (SUCCESS200HEADERS, JSONBODY)

        deviceid = uuid.uuid4()

        self.device.current_schedule(deviceid)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/" f"{deviceid}/current_schedule",
        )
        self.assertEqual(args[1], "GET")
        self.assertEqual(kwargs["body"], None)

    @patch("httplib2.Http.request")
    def test_event(self, mock):
        """Test if the event method works as expected."""
        mock.return_value = (SUCCESS200HEADERS, JSONBODY)

        deviceid = uuid.uuid4()
        starttime = 1414818000000
        endtime = 1415739608103

        self.device.event(deviceid, starttime, endtime)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0],
            f"{BASE_API_URL}/device/"
            f"{deviceid}/event?startTime="
            f"{starttime}&endTime="
            f"{endtime}",
        )
        self.assertEqual(args[1], "GET")
        self.assertEqual(kwargs["body"], None)

    @patch("httplib2.Http.request")
    def test_forecast(self, mock):
        """Test if the forecast method works as expected."""
        mock.return_value = (SUCCESS200HEADERS, JSONBODY)

        deviceid = uuid.uuid4()

        self.device.forecast(deviceid)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/" f"{deviceid}/forecast?units=US",
        )
        self.assertEqual(args[1], "GET")
        self.assertEqual(kwargs["body"], None)

        self.device.forecast(deviceid, "US")

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/" f"{deviceid}/forecast?units=US",
        )
        self.assertEqual(args[1], "GET")
        self.assertEqual(kwargs["body"], None)

        self.device.forecast(deviceid, "METRIC")

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0],
            f"{BASE_API_URL}/device/" f"{deviceid}/forecast?units=METRIC",
        )
        self.assertEqual(args[1], "GET")
        self.assertEqual(kwargs["body"], None)

        # Check that values should be within range.
        self.assertRaises(AssertionError, self.device.forecast, deviceid, "")

    @patch("httplib2.Http.request")
    def test_stop_water(self, mock):
        """Test if the stop water method works as expected."""
        mock.return_value = (SUCCESS204HEADERS, None)

        deviceid = uuid.uuid4()

        self.device.stop_water(deviceid)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/stop_water",
        )
        self.assertEqual(args[1], "PUT")
        self.assertEqual(kwargs["body"], {"id": deviceid})

    @patch("httplib2.Http.request")
    def test_rain_delay(self, mock):
        """Test if the rain delay method works as expected."""
        mock.return_value = (SUCCESS204HEADERS, None)

        deviceid = uuid.uuid4()
        duration = randrange(604800)

        self.device.rain_delay(deviceid, duration)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/rain_delay",
        )
        self.assertEqual(args[1], "PUT")
        self.assertEqual(
            kwargs["body"], {"id": deviceid, "duration": duration}
        )

        # Check that values should be within range.
        self.assertRaises(AssertionError, self.device.rain_delay, deviceid, -1)
        self.assertRaises(
            AssertionError, self.device.rain_delay, deviceid, 604801
        )

    @patch("httplib2.Http.request")
    def test_turn_on(self, mock):
        """Test if the turn on method works as expected."""
        mock.return_value = (SUCCESS204HEADERS, None)

        deviceid = uuid.uuid4()

        self.device.turn_on(deviceid)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/on",
        )
        self.assertEqual(args[1], "PUT")
        self.assertEqual(kwargs["body"], {"id": deviceid})

    @patch("httplib2.Http.request")
    def test_turn_off(self, mock):
        """Test if the turn off method works as expected."""
        mock.return_value = (SUCCESS204HEADERS, None)

        deviceid = uuid.uuid4()

        self.device.turn_off(deviceid)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/off",
        )
        self.assertEqual(args[1], "PUT")
        self.assertEqual(kwargs["body"], {"id": deviceid})

    @patch("httplib2.Http.request")
    def test_pause_zone_run(self, mock):
        """Test if the pause zone run method works as expected."""
        mock.return_value = (SUCCESS204HEADERS, None)

        deviceid = uuid.uuid4()
        duration = randrange(3600)

        self.device.pause_zone_run(deviceid, duration)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/pause_zone_run",
        )
        self.assertEqual(args[1], "PUT")
        self.assertEqual(
            kwargs["body"], {"id": deviceid, "duration": duration}
        )

        # Check that values should be within range.
        self.assertRaises(
            AssertionError, self.device.pause_zone_run, deviceid, -1
        )
        self.assertRaises(
            AssertionError, self.device.pause_zone_run, deviceid, 3601
        )

    @patch("httplib2.Http.request")
    def test_resume_zone_run(self, mock):
        """Test if the resume zone run method works as expected."""
        mock.return_value = (SUCCESS204HEADERS, None)

        deviceid = uuid.uuid4()

        self.device.resume_zone_run(deviceid)

        args, kwargs = mock.call_args

        # Check that the mock funciton is called with the rights args.
        self.assertEqual(
            args[0], f"{BASE_API_URL}/device/resume_zone_run",
        )
        self.assertEqual(args[1], "PUT")
        self.assertEqual(kwargs["body"], {"id": deviceid})
