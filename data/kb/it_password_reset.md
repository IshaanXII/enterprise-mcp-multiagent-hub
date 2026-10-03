# Password Reset SOP (IT-001)

**Applies to:** Active Directory, Okta SSO, VPN users.

**Steps:**
1. Verify user identity via employee ID + manager email.
2. Check account status in CRM: if `locked`, unlock via `unlock_account`.
3. Reset in Okta: Temporary password valid 24h, enforce MFA re-enrol.
4. If user reports phishing after reset, escalate to P1 Security.
5. Log ticket with action `password_reset`.

**SLA:** P3 (24h), P2 (8h) if user is C-level or production blocked.
**RAG source:** Use this doc for any ticket mentioning password, locked out, OTP, MFA failure.
