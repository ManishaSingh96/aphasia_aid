def test_sample_function(sample_fixture: str) -> None:
    """A sample test function that uses a fixture."""
    # S101: For simple equality checks, assert is idiomatic.
    # For more complex scenarios, pytest's assertion helpers might be preferred.
    assert sample_fixture == "sample_data"  # noqa: S101
