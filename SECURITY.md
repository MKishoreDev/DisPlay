# 🔒 Security Policy

## 🛡️ Security Model

**DisPlay** is engineered with a strict zero-trust security architecture:

1. **Zero Credential Access**: DisPlay does not request, store, or transmit Discord tokens, passwords, or session cookies.
2. **Zero Network Tracking**: DisPlay makes standard, unauthenticated GET requests to Discord's public detectable applications endpoint (`https://discord.com/api/applications/detectable`). No user telemetry or analytics are collected.
3. **Local OS Execution**: Process image spoofing is performed purely through standard local OS process APIs without DLL injection, driver loading, or memory manipulation.

---

## 📩 Reporting a Vulnerability

If you discover a security vulnerability or potential risk within **DisPlay**, please follow these guidelines:

1. **Do NOT open a public GitHub issue** for undisclosed security vulnerabilities.
2. Send a private report detailing the vulnerability to **Kishore** via:
   - **Discord**: `@k4isszluv` (ID: `1137667373307011192`)
   - **GitHub Security Advisory**: Submit a private advisory via [DisPlay Security Advisories](https://github.com/MKishoreDev/DisPlay/security/advisories/new).

---

## ⏱️ Response Policy

- We aim to acknowledge valid vulnerability reports within **48 hours**.
- Fixes or mitigations will be prioritized and published in a security patch release as soon as verified.

---

<div align="center">

*Copyright © 2026 Kishore. Released under the [MIT License](LICENSE).*

</div>
