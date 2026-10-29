# OWASP Top 10 — Secure Coding Reference (Educational Summary)

This short reference is intended to support code-review learning, not to reproduce the full OWASP publication. OWASP Top 10 categories and editions can change; consult the official OWASP site for the current edition.

## Access control
Enforce authorization on the server for every protected resource and operation. Apply least privilege and deny by default.

## Security misconfiguration
Remove default credentials, disable debug mode in production, keep dependencies and services configured securely, and avoid exposing unnecessary endpoints.

## Software supply chain and vulnerable components
Track dependencies, update vulnerable packages, use trusted package sources, and review build and deployment integrity.

## Cryptographic failures
Protect sensitive data, use well-established cryptographic libraries, and avoid storing secrets or passwords in plaintext.

## Injection
Separate code/query structure from data. Use parameterized SQL, safe APIs, context-appropriate output encoding, and allow-listed operations.

## Insecure design
Use threat modeling, abuse cases, secure defaults, and security requirements early in development.

## Authentication failures
Use established authentication mechanisms, protect sessions, rate-limit sensitive flows, and implement secure account recovery.

## Integrity failures
Verify the integrity of critical updates, artifacts, and serialized data; avoid unsafe deserialization of untrusted content.

## Logging and monitoring failures
Record useful security events without logging secrets; protect logs and monitor suspicious activity.

## Exceptional conditions
Handle errors safely, avoid leaking internal details, and ensure failures do not bypass security controls.

## References
Use the official OWASP Top 10 and OWASP Cheat Sheet Series as the authoritative, current sources.
