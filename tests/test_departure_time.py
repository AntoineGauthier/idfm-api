from idfm_api.models import TrafficData


def _payload():
    return {
        "MonitoredVehicleJourney": {
            "DirectionName": [{"value": "Retour"}],
            "DestinationName": [{"value": "Paris Montparnasse"}],
            "DestinationRef": {"value": "destination"},
            "LineRef": {"value": "C01744"},
            "MonitoredCall": {
                "VehicleAtStop": False,
                "ArrivalPlatformName": {"value": "2"},
                "ExpectedArrivalTime": "2026-08-25T06:42:00.000Z",
                "ExpectedDepartureTime": "2026-08-25T06:43:00.000Z",
                "ArrivalStatus": "onTime",
            },
        }
    }


def test_departure_time_is_preferred_over_arrival_time():
    traffic = TrafficData.from_json(_payload())

    assert traffic.schedule.isoformat() == "2026-08-25T06:43:00+00:00"
