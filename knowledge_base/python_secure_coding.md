# Python Secure Coding Knowledge Base

## Input validation
Validate data at trust boundaries using explicit allow-lists, expected types, lengths, and formats. Reject unexpected values early. Validation complements rather than replaces context-specific protections.

## SQL injection
Never build SQL by concatenating user-controlled values. Use DB-API parameterized queries, for example `cursor.execute("SELECT * FROM users WHERE name = ?", (name,))` for SQLite. Placeholder syntax varies by database driver. Do not interpolate values into SQL strings.

## Secrets and passwords
Do not hard-code API keys, passwords, or tokens. Read secrets from environment variables or a managed secret store and keep `.env` files out of version control. Store passwords with a dedicated password-hashing algorithm such as Argon2id, bcrypt, or scrypt using appropriate parameters and unique salts; do not store plaintext passwords or use fast general-purpose hashes such as plain SHA-256.

## Unsafe evaluation and deserialization
Avoid `eval` and `exec` on untrusted input. Prefer constrained parsers such as JSON. Do not deserialize untrusted pickle data. Validate file paths and restrict file operations to intended directories.

## Exceptions and logging
Do not expose stack traces, credentials, or sensitive user data to end users. Log security-relevant events with access controls and avoid logging secrets. Handle errors without leaking internal implementation details.

## Cryptography and transport
Use maintained cryptographic libraries and modern, secure defaults. Do not invent cryptographic algorithms. Verify TLS certificates and use HTTPS for sensitive data in transit.

## References
Guidance is summarized for educational use. Consult the official Python documentation and OWASP Cheat Sheet Series for current, detailed recommendations.
