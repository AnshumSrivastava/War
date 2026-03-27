"""
test/test_service_result.py
QA tests for services.service_result.ServiceResult, ok(), and err()

Validates the contract that every service function must satisfy:
always returns a ServiceResult, never raises to the caller.
"""
import pytest
from services.service_result import ServiceResult, ok, err


class TestOk:
    def test_ok_sets_flag(self):
        r = ok({"x": 1})
        assert r.ok is True

    def test_ok_data_preserved(self):
        payload = {"entities": [1, 2, 3]}
        r = ok(payload)
        assert r.data == payload

    def test_ok_error_is_empty_string(self):
        r = ok(None)
        assert r.error == ""

    def test_ok_code_is_none(self):
        r = ok("anything")
        assert r.code is None

    def test_ok_no_args(self):
        r = ok()
        assert r.ok is True
        assert r.data is None

    def test_ok_with_list(self):
        r = ok([1, 2, 3])
        assert r.data == [1, 2, 3]

    def test_ok_with_string(self):
        r = ok("hello")
        assert r.data == "hello"


class TestErr:
    def test_err_sets_flag(self):
        r = err("something went wrong")
        assert r.ok is False

    def test_err_message_stored(self):
        r = err("map not loaded")
        assert r.error == "map not loaded"

    def test_err_data_is_none_by_default(self):
        r = err("oops")
        assert r.data is None

    def test_err_code_stored(self):
        r = err("not found", code="NOT_FOUND")
        assert r.code == "NOT_FOUND"

    def test_err_with_partial_data(self):
        """Services may return partial data on error (e.g. partial-success scenarios)."""
        r = err("partial failure", data={"partial": True})
        assert r.ok is False
        assert r.data == {"partial": True}

    def test_err_code_none_by_default(self):
        r = err("no code")
        assert r.code is None


class TestServiceResultDirect:
    def test_direct_construction_ok(self):
        r = ServiceResult(ok=True, data=42, error="", code=None)
        assert r.ok is True
        assert r.data == 42

    def test_direct_construction_error(self):
        r = ServiceResult(ok=False, data=None, error="bad", code="ERR")
        assert r.ok is False
        assert r.error == "bad"
        assert r.code == "ERR"

    def test_truthy_ok(self):
        """Consumers can use `if result.ok` pattern."""
        r = ok("data")
        if not r.ok:
            pytest.fail("result.ok should be truthy")

    def test_falsy_ok_on_error(self):
        r = err("bad")
        if r.ok:
            pytest.fail("result.ok should be falsy on error")
