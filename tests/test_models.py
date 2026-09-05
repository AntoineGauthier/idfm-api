import logging

from idfm_api import _deduplicate_traffic
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


def _traffic_payload(*, journey_ref, aimed_departure, expected_departure):
    payload = _base_payload()
    journey = payload["MonitoredVehicleJourney"]
    journey["DirectionName"] = [{"value": "A"}]
    journey["DestinationName"] = [{"value": "Gare de Rambouil"}]
    journey["DestinationRef"] = {"value": "rambouillet"}
    journey["LineRef"] = {"value": "C00177"}
    journey["FramedVehicleJourneyRef"] = {
        "DataFrameRef": {"value": "any"},
        "DatedVehicleJourneyRef": journey_ref,
    }
    call = journey["MonitoredCall"]
    call.pop("ExpectedArrivalTime", None)
    call["AimedDepartureTime"] = aimed_departure
    call["ExpectedDepartureTime"] = expected_departure
    call["DepartureStatus"] = "delayed"
    return payload


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


def test_duplicate_aimed_service_keeps_earliest_current_prediction():
    early_raw = _traffic_payload(
        journey_ref="SUDYV:VehicleJourney::1057:LOC",
        aimed_departure="2026-09-04T05:37:00.000Z",
        expected_departure="2026-09-04T05:37:00.000Z",
    )
    late_raw = _traffic_payload(
        journey_ref="SUDYV:VehicleJourney::1058:LOC",
        aimed_departure="2026-09-04T05:37:00.000Z",
        expected_departure="2026-09-04T05:39:00.000Z",
    )
    early = TrafficData.from_json(early_raw)
    late = TrafficData.from_json(late_raw)

    result = _deduplicate_traffic([(late, late_raw), (early, early_raw)])

    assert result == [early]


def test_distinct_aimed_services_remain_separate():
    first_raw = _traffic_payload(
        journey_ref="SUDYV:VehicleJourney::1057:LOC",
        aimed_departure="2026-09-04T05:37:00.000Z",
        expected_departure="2026-09-04T05:38:00.000Z",
    )
    second_raw = _traffic_payload(
        journey_ref="SUDYV:VehicleJourney::1059:LOC",
        aimed_departure="2026-09-04T06:42:00.000Z",
        expected_departure="2026-09-04T06:55:00.000Z",
    )
    first = TrafficData.from_json(first_raw)
    second = TrafficData.from_json(second_raw)

    result = _deduplicate_traffic([(second, second_raw), (first, first_raw)])

    assert result == [first, second]


def test_records_without_aimed_departure_are_not_grouped():
    first_raw = _base_payload()
    second_raw = _base_payload()
    first_raw["MonitoredVehicleJourney"]["DestinationRef"] = {"value": "one"}
    second_raw["MonitoredVehicleJourney"]["DestinationRef"] = {"value": "two"}
    second_raw["MonitoredVehicleJourney"]["MonitoredCall"][
        "ExpectedArrivalTime"
    ] = "2026-08-25T07:42:00.000Z"
    first = TrafficData.from_json(first_raw)
    second = TrafficData.from_json(second_raw)

    result = _deduplicate_traffic([(second, second_raw), (first, first_raw)])

    assert result == [first, second]
