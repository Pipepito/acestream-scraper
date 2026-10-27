"""Target reservations share FIFO admission with scheduled maintenance."""
import threading
from concurrent.futures import ThreadPoolExecutor
from app.services.task_service import TaskService


def test_manual_and_scheduled_targets_coalesce_in_both_orders():
    service = TaskService()
    service.start()
    entered, release, prepared, completed = threading.Event(), threading.Event(), threading.Event(), threading.Event()
    order = []
    scheduled_enqueued = threading.Event()
    original_persist = service.persist_current_state
    def persist(job_id, state):
        original_persist(job_id, state)
        if job_id == 'url_scraping' and state['status'] == 'waiting':
            scheduled_enqueued.set()
    service.persist_current_state = persist
    def prepare(run_id, target):
        prepared.set()
        return {'run_id': run_id, **target}
    def execute(target, shutdown):
        order.append('manual')
        completed.set()
    def blocker():
        entered.set()
        assert release.wait(5)
        order.append('epg')
    service.register_maintenance_targets('url_scraping', snapshot=lambda: [('saved_search:1', {})],
        prepare=prepare, finish=lambda _: None, argument='targets')
    try:
        with ThreadPoolExecutor(2) as pool:
            first = pool.submit(service._instrument_task('epg_refresh', blocker, maintenance=True))
            assert entered.wait(5)
            run_id = service.submit_maintenance_target('saved_search:1', {}, prepare=prepare, execute=execute, finish=lambda _: None)
            assert service.submit_maintenance_target('saved_search:1', {}, prepare=prepare, execute=execute, finish=lambda _: None) == run_id
            scheduled = pool.submit(service._instrument_task('url_scraping', lambda targets: (order.append('urls'), targets)[1], maintenance=True))
            assert scheduled_enqueued.wait(5)
            release.set()
            first.result(5)
            assert scheduled.result(5) == []
            assert completed.wait(5)
        assert order == ['epg', 'manual', 'urls']
        # Scheduled-first reservation exists while its enclosing URL work runs.
        entered.clear(); release.clear()
        with ThreadPoolExecutor(1) as pool:
            scheduled = pool.submit(service._instrument_task('url_scraping', lambda targets: (blocker(), targets)[1], maintenance=True))
            assert entered.wait(5)
            existing = service._target_reservations['saved_search:1']['run_id']
            assert service.submit_maintenance_target('saved_search:1', {}, prepare=prepare, execute=execute, finish=lambda _: None) == existing
            release.set()
            assert len(scheduled.result(5)) == 1
        assert not service._target_reservations and not service._maintenance_queue
    finally:
        release.set()
        service.shutdown()


def test_completion_persistence_failure_releases_all_targets_and_fifo():
    service = TaskService()
    finished = []
    def finish(target):
        finished.append(target['id'])
        raise RuntimeError('state store unavailable')
    service.register_maintenance_targets('url_scraping',
        snapshot=lambda: [(str(i), {'id': i}) for i in range(2)],
        prepare=lambda run_id, target: dict(target, run_id=run_id), finish=finish, argument='targets')
    runner = service._instrument_task('url_scraping', lambda targets: len(targets), maintenance=True)
    assert runner() == 2
    assert finished == [0, 1]
    assert not service._target_reservations and not service._maintenance_queue


def test_shutdown_releases_waiting_manual_target_without_execution():
    service = TaskService()
    service.start()
    executed, finished = threading.Event(), threading.Event()
    blocker = object()
    with service._maintenance_condition:
        service._maintenance_queue.append(blocker)
    service.submit_maintenance_target('saved_search:1', {},
        prepare=lambda run_id, target: dict(target, run_id=run_id),
        execute=lambda *args: executed.set(), finish=lambda target: finished.set())
    service.shutdown()
    assert finished.is_set() and not executed.is_set()
    assert not service._target_reservations and not service._target_threads
    assert list(service._maintenance_queue) == [blocker]
    service._release_maintenance(blocker)


def test_snapshot_failure_records_failure_without_reserving_work():
    import pytest
    service = TaskService()
    def unavailable():
        raise RuntimeError('snapshot unavailable')
    service.register_maintenance_targets('url_scraping', snapshot=unavailable,
        prepare=lambda *args: None, finish=lambda *args: None, argument='targets')
    with pytest.raises(RuntimeError, match='snapshot unavailable'):
        service._instrument_task('url_scraping', lambda **kw: None, maintenance=True)()
    assert service._task_states['url_scraping']['status'] == 'error'
    assert not service._target_reservations and not service._maintenance_queue


def test_failed_persistence_releases_admission():
    import pytest
    service = TaskService()
    service.start()
    try:
        with pytest.raises(RuntimeError):
            service.submit_maintenance_target('x', {}, prepare=lambda *args: (_ for _ in ()).throw(RuntimeError()), execute=lambda *args: None, finish=lambda *args: None)
        assert not service._target_reservations and not service._maintenance_queue
    finally:
        service.shutdown()
