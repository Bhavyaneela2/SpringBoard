# Starter Secure Coding Knowledge Base

## SQL injection and parameterized queries
SQL injection can occur when untrusted input is combined with SQL query text. Prefer parameterized queries or prepared statements, where query structure is separate from values. Validate input for business rules, but do not treat validation as a substitute for parameterization.

## Secrets and credentials
Do not commit passwords, API keys, access tokens, or private keys to source control. Load credentials from environment variables or a dedicated secrets manager. If a real secret was exposed, revoke or rotate it; deleting the line alone does not invalidate the old credential.

## Cross-site scripting (XSS)
XSS can happen when untrusted data is interpreted as HTML or JavaScript in a browser. Prefer safe text APIs, context-aware output encoding, and framework protections. If rich HTML is required, use a vetted sanitizer configured for the intended context.

## Input validation
Validate data at trust boundaries using explicit allow-lists and expected types, lengths, and formats. Reject unexpected values early. Validation should be paired with context-specific protections such as SQL parameters and output encoding.

## Unsafe dynamic evaluation
Avoid evaluating user-controlled text as program code. Prefer explicit parsing, constrained data formats, and allow-listed operations. Dynamic execution can create injection and code execution risks.

## Insecure deserialization
Do not deserialize untrusted data into arbitrary objects. Prefer simpler formats such as JSON and validate their schemas. Treat data from external sources as untrusted even when it comes from internal systems.

## Logging and debug output
Use structured logging with appropriate levels. Avoid logging passwords, access tokens, sensitive personal information, or raw confidential payloads. Remove temporary debug statements before production.

## Severity and verification
Severity depends on exploitability, exposure, privileges, and impact. Automated findings are signals for review, not proof of exploitability. Verify evidence, assess context, document false positives, and test fixes.
