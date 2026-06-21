import io
import re
import argparse
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

try:
    import anthropic as _anthropic_module
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _anthropic_module = None  # type: ignore[assignment]
    _ANTHROPIC_AVAILABLE = False

_SYSTEM_PROMPT = (
    'You are a CI failure analyst. '
    'Given raw CI log context, respond with exactly:\n'
    '1. Probable cause (1-2 sentences)\n'
    '2. Affected files or components\n'
    '3. Suggested fix (1-3 actionable steps)\n'
    'Be specific. Do not repeat the log verbatim.'
)

_REDACT_PATTERNS = [
    (re.compile(r'ghp_[A-Za-z0-9]{36,}'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'ghs_[A-Za-z0-9]{36,}'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'github_pat_[A-Za-z0-9_]{36,}'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'(?i)(password|token|secret|api[_-]?key)\s*[=:]\s*(\S+)'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)bearer\s+\S+'), 'Bearer [REDACTED]'),
    (re.compile(r'(?i)(https?://)([^:@/\s]+):([^@\s]+)@'), r'\1[REDACTED]:[REDACTED]@'),
]

_FAILURE_RE = re.compile(
    r'(error|exception|traceback|assert|FAILED|##\[error\])',
    re.IGNORECASE,
)

_CONTEXT_LINES = 3
_FALLBACK_TAIL = 20


def redact_sensitive(text: str) -> str:
    for pattern, replacement in _REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def extract_failure_context(log_text: str, context_lines: int = _CONTEXT_LINES) -> str:
    lines = log_text.splitlines()
    if not lines:
        return ''

    relevant: set[int] = set()
    for i, line in enumerate(lines):
        if _FAILURE_RE.search(line):
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            relevant.update(range(start, end))

    if not relevant:
        return '\n'.join(lines[-_FALLBACK_TAIL:])

    result: list[str] = []
    prev: int | None = None
    for i in sorted(relevant):
        if prev is not None and i > prev + 1:
            result.append('...')
        result.append(lines[i])
        prev = i

    return '\n'.join(result)


def analyze_log(log_text: str, context_lines: int = _CONTEXT_LINES) -> str:
    cleaned = redact_sensitive(log_text)
    return extract_failure_context(cleaned, context_lines)


def summarize_failure(
    context: str,
    model: str = 'claude-haiku-4-5-20251001',
    max_tokens: int = 1024,
) -> str:
    if not _ANTHROPIC_AVAILABLE:
        raise ImportError('anthropic package required: pip install anthropic')
    client = _anthropic_module.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': context}],
    )
    return message.content[0].text


def _download_with_redirect(req: urllib.request.Request) -> bytes:
    # GitHub /logs returns 302 to a signed S3/Azure URL; follow without forwarding auth headers
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        location = exc.headers.get('Location')
        if not location:
            raise ValueError('Redirect response missing Location header') from exc
        with urllib.request.urlopen(location) as response:
            return response.read()


def _extract_logs_from_zip(zip_bytes: bytes) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith('.txt'):
                content = zf.read(name).decode('utf-8', errors='replace')
                parts.append(f'=== {name} ===\n{content}')
    return '\n'.join(parts)


def fetch_run_log(run_id: int, repo: str, token: str) -> str:
    url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/logs'
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        },
    )
    zip_bytes = _download_with_redirect(req)
    return _extract_logs_from_zip(zip_bytes)


def main() -> None:
    parser = argparse.ArgumentParser(description='Extract failure context from a CI log file.')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--log-file', type=Path)
    source.add_argument('--run-id', type=int)
    parser.add_argument('--repo', help='owner/repo (required with --run-id)')
    parser.add_argument('--token', help='GitHub token (required with --run-id)')
    parser.add_argument('--context-lines', type=int, default=_CONTEXT_LINES)
    parser.add_argument('--summarize', action='store_true', help='Send failure context to Claude API')
    parser.add_argument('--model', default='claude-haiku-4-5-20251001', help='Claude model for --summarize')
    args = parser.parse_args()

    if args.log_file:
        log_text = args.log_file.read_text(encoding='utf-8', errors='replace')
    else:
        if not args.repo or not args.token:
            parser.error('--repo and --token are required when using --run-id')
        log_text = fetch_run_log(args.run_id, args.repo, args.token)

    result = analyze_log(log_text, args.context_lines)
    if args.summarize:
        try:
            result = summarize_failure(result, model=args.model)
        except ImportError as exc:
            parser.error(str(exc))
    print(result)


if __name__ == '__main__':
    main()
