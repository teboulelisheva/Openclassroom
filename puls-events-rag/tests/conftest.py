"""
Configuration pytest — Puls-Events RAG
"""
import pytest
import os


def pytest_configure(config):
    """Configuration globale pytest."""
    os.makedirs("logs", exist_ok=True)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Affiche un résumé lisible à la fin des tests."""
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    total = passed + failed + skipped

    print(f"\n{'='*50}")
    print(f"RESUME TESTS PULS-EVENTS RAG")
    print(f"{'='*50}")
    print(f"Total   : {total}")
    print(f"Passes  : {passed}")
    print(f"Echecs  : {failed}")
    print(f"Ignores : {skipped}")
    print(f"Taux    : {passed/total*100:.0f}%" if total > 0 else "Taux : N/A")
    print(f"{'='*50}")
