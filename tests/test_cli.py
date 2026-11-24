from support_agent.cli import main


def test_cli_answers_offline_without_a_key(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    exit_code = main(["What is the status of booking BK-1001?"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "confirmed" in captured.out
    assert "Lisbon" in captured.out
    assert "lookup_booking" in captured.out
    assert captured.err == ""
