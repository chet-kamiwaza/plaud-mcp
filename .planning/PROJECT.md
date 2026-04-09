# Plaud Linux Client

## What This Is

A custom Linux desktop client for the Plaud AI cloud service. It authenticates with Plaud's cloud API, then lets users browse and view their past recordings, transcripts, and AI-generated summaries. Built for Linux users who have Plaud recordings in the cloud but no native Linux app to access them.

## Core Value

A Linux user can log into their Plaud account and read their recordings, transcripts, and AI summaries.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can authenticate with the Plaud cloud service on Linux
- [ ] User can view their list of past recordings
- [ ] User can view transcripts for individual recordings
- [ ] User can view AI-generated summaries/notes for recordings
- [ ] Session persists across app restarts (token stored locally)
- [ ] User can log out

### Out of Scope

- Audio recording functionality — macOS-specific native modules; not the goal
- System audio capture — macOS TCC + Core Audio, no Linux port planned
- Meeting auto-detection — requires audio_monitor native module, not needed
- macOS/Windows builds — building for Linux only
- Uploading recordings — no recording functionality means no upload needed

## Context

**Source analysis:** Reverse-engineered from the compiled macOS Plaud Electron app (v1.0.5, `ai.plaud.desktop.plaud`). Source maps in the ASAR bundle allowed full TypeScript recovery (263 files, 729KB source). Extracted source lives in `/tmp/plaud-src/`.

**API:** Base URL `https://api.plaud.ai`. All requests require:
- `Authorization: bearer <token>`
- `edit-from: desktop`
- `app-platform: desktop`
- `app-versionNumber: <semver>`
- `app-language: <lang-code>` (e.g. `en-US`)
- `X-Device-Id: <device-uuid>`

Domain can change dynamically — API returns status `-302` with a new domain when a redirect is needed.

**Auth flow:** Browser opens `https://web.plaud.ai/` → web app redirects to `plaud://auth?auth_code=<code>` → desktop app intercepts the URL scheme → `POST /auth/access-token-auth-code` with `{ client_id: "desktop", auth_code, desktop_uuid }` → receives `access_token` → stored as `bearer <token>`.

**Known API endpoints:**
- `POST /auth/access-token-auth-code` — exchange auth code for token
- `POST /auth/access-token-logout` — invalidate token
- `GET /user/me` — user profile + membership type
- `GET /user/workflows` — user AutoFlow workflow configurations

**Content location:** All recordings, transcripts, and summaries live at `https://web.plaud.ai/file/<fileId>`. The macOS desktop app opens that URL in the system browser when the user clicks "View Notes."

**Status codes:**
- `0` — success
- `-10000` — auth error (token invalid/expired)
- `-302` — domain change (update base URL and retry)
- `-9999` — application error with user-visible alert message

**Linux URL scheme registration:** Unlike macOS (NSApp URL scheme), Linux requires `xdg-mime` / `.desktop` file registration for `plaud://` protocol handling.

## Constraints

- **API**: Must use `https://api.plaud.ai` — no public API docs; derived from reverse engineering
- **Auth**: Must implement the `plaud://` OAuth callback protocol on Linux
- **Platform**: Linux-first; macOS/Windows not targeted in this milestone

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Custom API client (not thin Electron shell) | More control, lighter, no macOS recording code baggage | — Pending |
| Reuse extracted TypeScript API client code | Already battle-tested, same auth/fetch logic | — Pending |
| Stack TBD (Electron vs Tauri vs CLI) | Research needed to pick best fit for Linux desktop | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-08 after initialization*
