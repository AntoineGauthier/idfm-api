import logging

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


def test_missing_expected_time_is_logged_and_still_discarded(caplog):
    payload = _base_payload()
    journey = payload["MonitoredVehicleJourney"]
    journey["DatedVehicleJourneyRef"] = {"value": "journey-123"}
    call = journey["MonitoredCall"]
    del call["ExpectedArrivalTime"]
    call["AimedDepartureTime"] = "2026-08-25T06:40:00.000Z"
    call["DepartureStatus"] = "delayed"

    with caplog.at_level(logging.WARNING, logger="idfm_api.models"):
        traffic = TrafficData.from_json(payload)

    assert traffic is None
    assert "IDFM MISSING EXPECTED TIME" in caplog.text
    assert "AimedDepartureTime" in caplog.text
    assert "journey-123" in caplog.text
    assert "delayed" in caplog.text
