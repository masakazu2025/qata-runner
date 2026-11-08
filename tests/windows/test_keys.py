"""keys.feature の手順。"""

from pytest_bdd import parsers, scenarios, then, when

from qata_runner.windows import to_send_keys

scenarios("keys.feature")


@when(parsers.parse('キー "{key}" を書き換える'), target_fixture="written")
def rewrite(key: str) -> str:
    return to_send_keys(key)


@then(parsers.parse('"{expected}" になる'))
def written_is(written: str, expected: str) -> None:
    assert written == expected
