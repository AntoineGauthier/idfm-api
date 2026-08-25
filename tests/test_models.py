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
