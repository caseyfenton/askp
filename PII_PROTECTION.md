# PII Protection for ASKP

ASKP now includes built-in PII (Personally Identifiable Information) validation to prevent accidentally sending sensitive data to external APIs.

## Features

- **Automatic Detection**: Scans queries for common PII patterns before sending to Perplexity API
- **Configurable**: Customize patterns, severity levels, and behavior via config file
- **Multiple Modes**: Block, warn, or silent mode operation
- **Whitelist Support**: Explicitly allow certain patterns
- **Custom Patterns**: Add your own regex patterns for domain-specific PII

## Quick Start

### Check Configuration

```bash
askp --pii-config
```

Shows current PII validation status, mode, and number of active patterns.

### Test PII Detection

```bash
# This will be blocked
askp "My email is john.doe@example.com"

# Bypass PII check for a single query (use with caution)
askp --no-pii-check "My email is john.doe@example.com"
```

## Default Patterns Detected

- **Email addresses**: `user@domain.com`
- **US phone numbers**: `(555) 123-4567`, `555-123-4567`
- **Social Security Numbers**: `123-45-6789`
- **Credit card numbers**: Visa, MasterCard, Amex, Discover
- **IP addresses**: `192.168.1.1`
- **API keys/tokens**: `api_key=ABC123...`
- **Passwords**: `password=secret123`
- **AWS keys**: `AKIAIOSFODNN7EXAMPLE`
- **Private keys**: `-----BEGIN PRIVATE KEY-----`
- **JWT tokens**: `eyJ...`

## Configuration

### Config File Location

`~/.askp/pii_config.json`

### Configuration Options

```json
{
  "enabled": true,
  "mode": "block",
  "patterns": { ... },
  "whitelist": [],
  "custom_patterns": {}
}
```

#### Modes

- **block** (default): Prevents queries with PII from being sent
- **warn**: Shows warning but allows query to proceed
- **silent**: No validation performed

#### Edit Configuration

```bash
# Using your preferred editor
nano ~/.askp/pii_config.json
vim ~/.askp/pii_config.json
code ~/.askp/pii_config.json
```

### Disable PII Validation Globally

Edit `~/.askp/pii_config.json` and set:
```json
{
  "enabled": false
}
```

### Change Mode to Warning Only

Edit `~/.askp/pii_config.json` and set:
```json
{
  "mode": "warn"
}
```

### Add Custom Patterns

```json
{
  "custom_patterns": {
    "employee_id": {
      "pattern": "EMP\\d{6}",
      "description": "Employee ID",
      "severity": "medium"
    },
    "internal_ip": {
      "pattern": "10\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}",
      "description": "Internal IP address",
      "severity": "low"
    }
  }
}
```

### Whitelist Specific Patterns

```json
{
  "whitelist": [
    "example\\.com$",
    "test@.*\\.test$"
  ]
}
```

Whitelist entries are regex patterns. Matches will be excluded from PII detection.

## Severity Levels

- **critical**: SSN, credit cards, private keys, passwords
- **high**: Email addresses, phone numbers, API tokens, JWT
- **medium**: IP addresses
- **low**: Custom patterns (configurable)

## CLI Options

### View PII Configuration

```bash
askp --pii-config
```

### Bypass PII Check for Single Query

```bash
askp --no-pii-check "query with sensitive data"
```

**Warning**: Use `--no-pii-check` sparingly and only when you're certain the data should be sent externally.

## Examples

### Blocked Query Example

```bash
$ askp "My SSN is 123-45-6789"

🚨 PII DETECTED IN QUERY

• Social Security Number (1 match)
  → 12******89

Query blocked. Remove sensitive data to proceed.
To configure: edit ~/.askp/pii_config.json
```

### Warning Mode Example

```bash
# After setting mode: "warn" in config
$ askp "Contact me at user@company.com"

⚠️  PII DETECTED IN QUERY

• Email address (1 match)
  → us************om

⚠️  Warning: Proceeding with PII in query

# Query proceeds despite PII detection
```

### Multiple PII Detected

```bash
$ askp "Call 555-1234 or email test@example.com for API key abc123xyz"

🚨 PII DETECTED IN QUERY

• Email address (1 match)
  → te************om
• US phone number (1 match)
  → 55******34
• API key or token (1 match)
  → ab******yz

Query blocked. Remove sensitive data to proceed.
```

## Integration with Git Hooks

This PII protection is designed to work similarly to git pre-commit hooks:

- **Automatic**: Runs on every query before API call
- **Configurable**: Customize via config file
- **Bypassable**: Use `--no-pii-check` when needed (like `git commit --no-verify`)
- **Persistent**: Settings stored in `~/.askp/` directory

## Best Practices

1. **Keep defaults enabled**: The default patterns catch most common PII
2. **Add custom patterns**: For organization-specific sensitive data
3. **Use warn mode for testing**: When developing new patterns
4. **Review config regularly**: Keep patterns up-to-date
5. **Educate team**: Make sure all users understand PII protection

## Troubleshooting

### False Positives

If legitimate queries are being blocked:

1. Add pattern to whitelist in config
2. Temporarily use `--no-pii-check` flag
3. Adjust pattern regex to be more specific
4. Change mode to "warn" to see what's triggering

### False Negatives

If PII isn't being caught:

1. Add custom pattern for your specific use case
2. Test pattern with sample data
3. Set severity level appropriately
4. Report missing patterns as feature request

## Security Considerations

- **Not foolproof**: PII detection uses regex patterns which may not catch all variations
- **No guarantee**: This is a best-effort protection mechanism
- **User responsibility**: Always review queries before sending
- **Audit logs**: Consider logging blocked queries for compliance
- **Sensitive contexts**: Use additional protections in regulated environments

## Disabling (Not Recommended)

To completely disable PII protection:

```bash
# Edit config file
nano ~/.askp/pii_config.json

# Set enabled to false
{
  "enabled": false
}
```

Or use `--no-pii-check` on every query (not recommended for regular use).

## Contributing

Found a PII pattern that should be included by default? Submit a PR or issue with:
- Description of the PII type
- Regex pattern
- Sample test cases (anonymized)
- Suggested severity level

---

**Remember**: This feature helps prevent accidental leakage of sensitive data, but it's not a substitute for careful data handling practices. Always review queries before sending to external APIs.
