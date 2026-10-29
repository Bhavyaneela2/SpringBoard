# Java Secure Coding Knowledge Base

## SQL injection
Use `PreparedStatement` with bind parameters rather than concatenating user-controlled values into SQL. Example: `PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE name = ?"); ps.setString(1, name);`. Parameterize values; allow-list identifiers such as sort-column names because SQL parameters generally cannot represent identifiers.

## Input validation
Validate untrusted input at application boundaries. Use allow-lists, expected types, length limits, and format checks. Do not rely on validation alone to prevent injection; use context-specific APIs and parameterization.

## Secrets and passwords
Do not hard-code credentials, API keys, or tokens in source code. Use environment variables or a managed secrets system and keep local secret files out of version control. Passwords should be stored using a dedicated password-hashing function such as Argon2id, bcrypt, or scrypt, with unique salts and appropriate work factors—not plaintext or a fast general-purpose hash.

## Command and path injection
Avoid constructing shell commands from untrusted input. Prefer APIs that accept argument arrays and avoid invoking a shell. Normalize and validate file paths, and ensure resolved paths remain inside the intended directory.

## Authentication and authorization
Apply authorization checks on every protected operation, not only in the UI. Use established authentication libraries, least privilege, secure session handling, and safe password-reset flows. Fail closed when access checks fail.

## Cryptography and transport
Use standard, maintained cryptographic libraries and secure defaults. Do not design custom cryptography. Protect sensitive data in transit with TLS and verify certificates.

## Errors and logging
Do not expose stack traces or sensitive details to clients. Avoid logging passwords, tokens, or personal data. Restrict access to logs and monitor security-relevant events.

## References
Guidance is summarized for educational use. Consult the official Java documentation, OWASP Cheat Sheet Series, and OWASP Top 10 for current, detailed recommendations.
