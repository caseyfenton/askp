#!/usr/bin/env python3
"""
PII (Personally Identifiable Information) validation for ASKP queries.
Prevents sensitive data from being sent to external APIs.
"""
import re
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from rich import print as rprint


class PIIValidator:
    """Validates queries for PII and sensitive data before sending to API."""

    # Default PII patterns
    DEFAULT_PATTERNS = {
        "email": {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "description": "Email address",
            "severity": "high"
        },
        "phone_us": {
            "pattern": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            "description": "US phone number",
            "severity": "high"
        },
        "ssn": {
            "pattern": r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b',
            "description": "Social Security Number",
            "severity": "critical"
        },
        "credit_card": {
            "pattern": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            "description": "Credit card number",
            "severity": "critical"
        },
        "ip_address": {
            "pattern": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            "description": "IP address",
            "severity": "medium"
        },
        "api_key": {
            "pattern": r'\b(?:api[_-]?key|apikey|api[_-]?token|access[_-]?token)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?',
            "description": "API key or token",
            "severity": "critical"
        },
        "password": {
            "pattern": r'\b(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']{8,})["\']?',
            "description": "Password",
            "severity": "critical"
        },
        "aws_key": {
            "pattern": r'\b(?:AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[0-9A-Z]{16}\b',
            "description": "AWS access key",
            "severity": "critical"
        },
        "private_key": {
            "pattern": r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----',
            "description": "Private key",
            "severity": "critical"
        },
        "jwt": {
            "pattern": r'\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b',
            "description": "JWT token",
            "severity": "high"
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize validator with config from file or defaults."""
        self.config_path = config_path or os.path.expanduser("~/.askp/pii_config.json")
        self.config = self._load_config()
        self.patterns = self._compile_patterns()

    def _load_config(self) -> Dict:
        """Load PII validation config from file or create default."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # Default configuration
        default_config = {
            "enabled": True,
            "mode": "block",  # "block", "warn", or "silent"
            "patterns": self.DEFAULT_PATTERNS,
            "whitelist": [],  # Patterns to explicitly allow
            "custom_patterns": {}  # User-defined patterns
        }

        # Create config directory if needed
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        # Save default config
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except OSError:
            pass

        return default_config

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns for efficiency."""
        compiled = {}

        # Compile default patterns
        for name, config in self.config.get("patterns", {}).items():
            try:
                compiled[name] = re.compile(config["pattern"], re.IGNORECASE)
            except re.error:
                pass

        # Compile custom patterns
        for name, config in self.config.get("custom_patterns", {}).items():
            try:
                compiled[f"custom_{name}"] = re.compile(config["pattern"], re.IGNORECASE)
            except re.error:
                pass

        return compiled

    def validate(self, query: str) -> Tuple[bool, List[Dict]]:
        """
        Validate query for PII.

        Returns:
            (is_safe, violations) where violations is list of detected PII
        """
        if not self.config.get("enabled", True):
            return (True, [])

        violations = []

        # Check against all patterns
        for name, pattern in self.patterns.items():
            matches = pattern.findall(query)
            if matches:
                # Get pattern config
                pattern_name = name.replace("custom_", "")
                if name.startswith("custom_"):
                    pattern_config = self.config["custom_patterns"].get(pattern_name, {})
                else:
                    pattern_config = self.config["patterns"].get(name, {})

                violations.append({
                    "type": name,
                    "description": pattern_config.get("description", "Unknown PII"),
                    "severity": pattern_config.get("severity", "medium"),
                    "matches": matches if isinstance(matches, list) else [matches],
                    "count": len(matches) if isinstance(matches, list) else 1
                })

        # Check whitelist - remove any violations that match whitelist patterns
        whitelist = self.config.get("whitelist", [])
        if whitelist and violations:
            for pattern in whitelist:
                try:
                    whitelist_re = re.compile(pattern, re.IGNORECASE)
                    violations = [v for v in violations
                                if not any(whitelist_re.search(str(m)) for m in v["matches"])]
                except re.error:
                    pass

        is_safe = len(violations) == 0
        return (is_safe, violations)

    def format_violations(self, violations: List[Dict]) -> str:
        """Format violations for display."""
        if not violations:
            return ""

        lines = ["\n[bold red]🚨 PII DETECTED IN QUERY[/bold red]\n"]

        for v in violations:
            severity_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "cyan",
                "low": "dim"
            }.get(v["severity"], "white")

            lines.append(f"[{severity_color}]• {v['description']}[/{severity_color}] "
                        f"({v['count']} match{'es' if v['count'] > 1 else ''})")

            # Show first 3 matches (masked)
            for match in v["matches"][:3]:
                masked = self._mask_value(str(match))
                lines.append(f"  → {masked}")

        mode = self.config.get("mode", "block")
        if mode == "block":
            lines.append("\n[red]Query blocked. Remove sensitive data to proceed.[/red]")
            lines.append("[dim]To configure: edit ~/.askp/pii_config.json[/dim]")
        else:
            lines.append("\n[yellow]⚠️  Warning: Proceeding with PII in query[/yellow]")

        return "\n".join(lines)

    def _mask_value(self, value: str) -> str:
        """Mask a sensitive value for display."""
        if len(value) <= 4:
            return "***"
        return value[:2] + ("*" * (len(value) - 4)) + value[-2:]

    def should_block(self, violations: List[Dict]) -> bool:
        """Determine if query should be blocked based on violations and mode."""
        if not violations:
            return False

        mode = self.config.get("mode", "block")

        if mode == "silent":
            return False
        elif mode == "warn":
            return False
        else:  # "block"
            return True


def validate_query_pii(query: str, quiet: bool = False) -> bool:
    """
    Validate a query for PII. Returns True if safe to proceed.

    Args:
        query: The query string to validate
        quiet: Suppress output messages

    Returns:
        True if query is safe to send, False if blocked
    """
    validator = PIIValidator()
    is_safe, violations = validator.validate(query)

    if violations and not quiet:
        message = validator.format_violations(violations)
        rprint(message)

    if validator.should_block(violations):
        return False

    return True


def get_pii_config_path() -> str:
    """Get the path to the PII config file."""
    return os.path.expanduser("~/.askp/pii_config.json")


def disable_pii_validation():
    """Disable PII validation globally."""
    config_path = get_pii_config_path()
    validator = PIIValidator(config_path)
    validator.config["enabled"] = False

    with open(config_path, 'w') as f:
        json.dump(validator.config, f, indent=2)


def enable_pii_validation():
    """Enable PII validation globally."""
    config_path = get_pii_config_path()
    validator = PIIValidator(config_path)
    validator.config["enabled"] = True

    with open(config_path, 'w') as f:
        json.dump(validator.config, f, indent=2)
