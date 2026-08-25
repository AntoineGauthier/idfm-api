from idfm_api.models import TrafficData


def _base_payload():
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
                "ArrivalStatus": "onTime",
            },
        }
    }


def test_vehicle_features_are_preserved():
    payload = _base_payload()
    payload["MonitoredVehicleJourney"]["VehicleFeatureRef"] = ["shortTrain"]

    traffic = TrafficData.from_json(payload)

    assert traffic.vehicle_features == ["shortTrain"]


def test_missing_vehicle_features_returns_empty_list():
    payload = _base_payload()

    traffic = TrafficData.from_json(payload)

    assert traffic.vehicle_features == []


def test_departure_time_is_preferred_over_arrival_time():
    payload = _base_payload()
    payload["MonitoredVehicleJourney"]["MonitoredCall"][
        "ExpectedDepartureTime"
    ] = "2026-08-25T06:43:00.000Z"

    traffic = TrafficData.from_json(payload)

    assert traffic.schedule.isoformat() == "2026-08-25T06:43:00+00:00"
