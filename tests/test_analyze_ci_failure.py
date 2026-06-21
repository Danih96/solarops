import io
import zipfile
import pytest
from unittest.mock import MagicMock, patch
from analyze_ci_failure import (
    redact_sensitive,
    extract_failure_context,
    fetch_run_log,
    summarize_failure,
    _extract_logs_from_zip,
)


def _make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


class TestRedactSensitive:
    def test_redacts_github_pat_token(self):
        line = 'Cloning with token ghp_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8'
        result = redact_sensitive(line)
        assert '[REDACTED_GITHUB_TOKEN]' in result
        assert 'ghp_' not in result

    def test_redacts_server_github_token(self):
        line = 'auth: ghs_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8'
        result = redact_sensitive(line)
        assert '[REDACTED_GITHUB_TOKEN]' in result

    def test_redacts_password_equals(self):
        result = redact_sensitive('db password=supersecret123')
        assert 'supersecret123' not in result
        assert '[REDACTED]' in result

    def test_redacts_token_colon(self):
        result = redact_sensitive('token: mytoken123')
        assert 'mytoken123' not in result
        assert '[REDACTED]' in result

    def test_redacts_secret_case_insensitive(self):
        result = redact_sensitive('SECRET=abc123')
        assert 'abc123' not in result

    def test_redacts_bearer_token(self):
        result = redact_sensitive('Authorization: Bearer eyJhbGciOiJIUzI1NiJ9')
        assert 'eyJhbGciOiJIUzI1NiJ9' not in result
        assert 'Bearer [REDACTED]' in result

    def test_redacts_url_credentials(self):
        result = redact_sensitive('url: https://admin:password123@db.example.com/data')
        assert 'password123' not in result
        assert 'admin' not in result
        assert 'https://' in result

    def test_safe_text_unchanged(self):
        line = 'All tests passed in 2.3s'
        assert redact_sensitive(line) == line


class TestExtractFailureContext:
    def test_returns_lines_around_error(self):
        log = '\n'.join([
            'step 1 ok',
            'step 2 ok',
            'Error: connection refused',
            'step 4 ok',
            'step 5 ok',
        ])
        result = extract_failure_context(log, context_lines=1)
        assert 'Error: connection refused' in result
        assert 'step 2 ok' in result
        assert 'step 4 ok' in result

    def test_detects_failed_keyword(self):
        log = '\n'.join([
            'running tests',
            'FAILED tests/test_foo.py::test_bar - AssertionError',
            'done',
        ])
        result = extract_failure_context(log, context_lines=0)
        assert 'FAILED' in result

    def test_detects_traceback(self):
        log = '\n'.join([
            'Traceback (most recent call last):',
            '  File "app.py", line 10, in main',
            '    raise ValueError("bad input")',
            'ValueError: bad input',
        ])
        result = extract_failure_context(log)
        assert 'ValueError' in result
        assert 'Traceback' in result

    def test_falls_back_to_tail_when_no_errors(self):
        lines = [f'line {i}' for i in range(30)]
        log = '\n'.join(lines)
        result = extract_failure_context(log)
        assert 'line 29' in result
        assert 'line 0' not in result

    def test_empty_log_returns_empty_string(self):
        assert extract_failure_context('') == ''

    def test_inserts_ellipsis_between_gaps(self):
        lines = ['ok'] * 50
        lines[5] = 'Error: first'
        lines[40] = 'Error: second'
        log = '\n'.join(lines)
        result = extract_failure_context(log, context_lines=0)
        assert '...' in result

    def test_github_actions_error_marker(self):
        log = '\n'.join([
            'Run tests',
            '##[error]Process completed with exit code 1.',
            'Finished',
        ])
        result = extract_failure_context(log, context_lines=0)
        assert '##[error]' in result


class TestExtractLogsFromZip:
    def test_extracts_txt_files(self):
        zip_bytes = _make_zip({'1_job.txt': 'line 1\nline 2', '2_test.txt': 'line 3'})
        result = _extract_logs_from_zip(zip_bytes)
        assert 'line 1' in result
        assert 'line 3' in result

    def test_ignores_non_txt_files(self):
        zip_bytes = _make_zip({'data.json': '{"key": "value"}', 'log.txt': 'actual log'})
        result = _extract_logs_from_zip(zip_bytes)
        assert 'actual log' in result
        assert '{"key"' not in result

    def test_files_appear_in_sorted_order(self):
        zip_bytes = _make_zip({'2_second.txt': 'second', '1_first.txt': 'first'})
        result = _extract_logs_from_zip(zip_bytes)
        assert result.index('first') < result.index('second')

    def test_section_header_included(self):
        zip_bytes = _make_zip({'1_build.txt': 'build output'})
        result = _extract_logs_from_zip(zip_bytes)
        assert '=== 1_build.txt ===' in result


class TestFetchRunLog:
    def test_returns_log_text(self):
        zip_bytes = _make_zip({'1_build.txt': 'Error: build failed\n'})
        with patch('analyze_ci_failure._download_with_redirect', return_value=zip_bytes):
            result = fetch_run_log(run_id=12345, repo='owner/repo', token='fake-token')
        assert 'Error: build failed' in result

    def test_request_uses_bearer_token(self):
        zip_bytes = _make_zip({'1_build.txt': 'ok'})
        with patch('analyze_ci_failure._download_with_redirect', return_value=zip_bytes) as mock_dl:
            fetch_run_log(run_id=99, repo='owner/repo', token='mytoken')
        req = mock_dl.call_args[0][0]
        assert req.get_header('Authorization') == 'Bearer mytoken'

    def test_request_targets_correct_url(self):
        zip_bytes = _make_zip({'1_build.txt': 'ok'})
        with patch('analyze_ci_failure._download_with_redirect', return_value=zip_bytes) as mock_dl:
            fetch_run_log(run_id=42, repo='my-org/my-repo', token='t')
        req = mock_dl.call_args[0][0]
        assert 'my-org/my-repo' in req.full_url
        assert '/42/' in req.full_url


class TestSummarizeFailure:
    def _mock_response(self, text: str):
        msg = MagicMock()
        msg.content = [MagicMock(text=text)]
        return msg

    def test_returns_claude_response_text(self):
        mock_module = MagicMock()
        mock_module.Anthropic.return_value.messages.create.return_value = (
            self._mock_response('1. Probable cause: import error')
        )
        with patch('analyze_ci_failure._ANTHROPIC_AVAILABLE', True), \
             patch('analyze_ci_failure._anthropic_module', mock_module):
            result = summarize_failure('Error: ModuleNotFoundError')
        assert 'Probable cause' in result

    def test_passes_context_as_user_message(self):
        mock_module = MagicMock()
        mock_module.Anthropic.return_value.messages.create.return_value = (
            self._mock_response('analysis')
        )
        with patch('analyze_ci_failure._ANTHROPIC_AVAILABLE', True), \
             patch('analyze_ci_failure._anthropic_module', mock_module):
            summarize_failure('FAILED tests/test_foo.py')
        call_kwargs = mock_module.Anthropic.return_value.messages.create.call_args[1]
        assert call_kwargs['messages'][0]['content'] == 'FAILED tests/test_foo.py'

    def test_uses_correct_model(self):
        mock_module = MagicMock()
        mock_module.Anthropic.return_value.messages.create.return_value = (
            self._mock_response('ok')
        )
        with patch('analyze_ci_failure._ANTHROPIC_AVAILABLE', True), \
             patch('analyze_ci_failure._anthropic_module', mock_module):
            summarize_failure('context', model='claude-haiku-4-5-20251001')
        call_kwargs = mock_module.Anthropic.return_value.messages.create.call_args[1]
        assert call_kwargs['model'] == 'claude-haiku-4-5-20251001'

    def test_raises_import_error_when_not_available(self):
        with patch('analyze_ci_failure._ANTHROPIC_AVAILABLE', False):
            with pytest.raises(ImportError, match='pip install anthropic'):
                summarize_failure('some context')
