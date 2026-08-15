import threading
import time

from fprime_gds.common.history.chrono import ChronologicalHistory
from fprime_gds.common.testing_fw import predicates
from fprime_gds.common.testing_fw.api import IntegrationTestAPI


class TimedItem:
    def __init__(self, label, timestamp):
        self.label = label
        self.timestamp = timestamp

    def get_time(self):
        return self.timestamp

    def __repr__(self):
        return f"TimedItem({self.label!r}, {self.timestamp})"


def test_sequence_search_rescans_after_chronological_reorder():
    api = object.__new__(IntegrationTestAPI)
    api.logger = None
    history = ChronologicalHistory()

    first_received = TimedItem("first-received", 2)
    arrives_late = TimedItem("arrives-late", 1)
    final = TimedItem("final", 3)
    history.data_callback(first_received)

    def add_remaining_items():
        time.sleep(0.05)
        history.data_callback(arrives_late)
        time.sleep(0.2)
        history.data_callback(final)

    producer = threading.Thread(target=add_remaining_items)
    producer.start()
    try:
        sequence = [predicates.always_true() for _ in range(3)]
        results = api.find_history_sequence(sequence, history, timeout=1)
    finally:
        producer.join()

    assert results == [arrives_late, first_received, final]
    assert len({id(item) for item in results}) == 3
