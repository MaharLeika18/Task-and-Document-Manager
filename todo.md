# Task and Document Manager - Gap TODO

This file lists what the project still lacks to be a complete, production-ready task and document manager.

## P0 - Critical Gaps (Build/Ship Blockers)

- [ ] Implement real document management backend (current Files page is mostly static UI): upload API, storage integration, metadata in Firestore, download/preview, rename, move, delete.
- [ ] Add document-to-project/task linking so files are actually associated with work items.
- [ ] Add file security controls: file type allowlist, max size limits, malware scanning hook, secure filename handling.
- [ ] Add per-file and per-folder permissions (view/edit/delete) tied to project membership and roles.
- [ ] Remove all secrets/credential JSON files from repository and rotate exposed keys/service credentials.
- [ ] Add strict production configuration: `debug=False`, environment-based settings, secure cookie/session flags, trusted hosts.
- [ ] Add CSRF protection for form and JSON-mutating endpoints.
- [ ] Add server-side validation and sanitization for all user inputs (project/task names, descriptions, dates, member IDs).

## P1 - Core Product Completeness

### Task Management
- [ ] Add edit task flow (name, description, assignees, due date, priority, status).
- [ ] Add delete task flow with confirmation and audit trail.
- [ ] Add task description/details field (currently task model is minimal).
- [ ] Add task comments/discussion thread.
- [ ] Add task attachments.
- [ ] Add task checklist/subtasks.
- [ ] Add recurring tasks and reminders.
- [ ] Add task dependencies/blockers.
- [ ] Add assignee notifications and due-date reminders.

### Project Management
- [ ] Add edit project flow (name, description, dates, members, category, status).
- [ ] Add archive/delete project flow with restore option (soft delete).
- [ ] Add project-level notes/description history.
- [ ] Add project templates.
- [ ] Add project activity timeline (who changed what, when).

### Calendar
- [ ] Add robust timezone support across UI and backend.
- [ ] Add two-way calendar sync strategy (handle updates/deletions reliably, not only create/patch).
- [ ] Add recurring calendar events support.
- [ ] Add retry/failure handling and background jobs for calendar operations.

### Document Experience
- [ ] Add folder tree navigation and breadcrumbs.
- [ ] Add drag-and-drop uploads and multi-file upload progress.
- [ ] Add file versioning and version history.
- [ ] Add file preview (PDF/image/text) and inline open.
- [ ] Add full-text file/document search.
- [ ] Add tags/labels for documents.
- [ ] Add recycle bin/restore for deleted files.

## P1 - Access Control and Collaboration

- [ ] Introduce role-based access control (owner, admin, editor, viewer).
- [ ] Add project invitation/acceptance workflow.
- [ ] Add member removal/transfer ownership rules.
- [ ] Add mention system (@user) in comments.
- [ ] Add in-app notification center.
- [ ] Add email notifications digest/settings.

## P1 - Data Model and Integrity

- [ ] Enforce consistent schemas for users/projects/tasks/files in Firestore.
- [ ] Add server-side uniqueness constraints where required (e.g., project UID collision handling).
- [ ] Use Firestore transactions/batches for multi-step updates.
- [ ] Add created_at/updated_at timestamps for all entities.
- [ ] Add soft delete flags and retention policy.
- [ ] Add audit logging for security-sensitive and business-critical changes.

## P2 - UX and Frontend Quality

- [ ] Replace page reloads after task updates with optimistic UI updates.
- [ ] Add clear loading/empty/error states to all views.
- [ ] Add accessibility pass (keyboard navigation, ARIA labels, focus management, color contrast).
- [ ] Improve mobile behavior for dense project/task screens.
- [ ] Add pagination/virtualization for large project/task/file lists.
- [ ] Add advanced filters/sorting (owner, priority, due date, status, category, member).
- [ ] Add unified global search across projects, tasks, members, and files.

## P2 - Security Hardening

- [ ] Add rate limiting for auth and write endpoints.
- [ ] Add account lockout / suspicious login protections.
- [ ] Add secure headers (CSP, HSTS, X-Frame-Options, etc.).
- [ ] Add strict CORS policy.
- [ ] Add centralized error handling that avoids leaking internals.
- [ ] Add PII-conscious logging and log redaction.

## P2 - Engineering Quality

- [ ] Add automated tests: unit, integration, and end-to-end for auth/projects/tasks/files/calendar.
- [ ] Add CI pipeline (lint, test, security checks, build).
- [ ] Add linting/formatting/type checks for Python and JS.
- [ ] Refactor oversized template scripts into modular frontend files.
- [ ] Clean dependency lists (`requirements.txt` has duplicates/unused packages).
- [ ] Add API contract docs (request/response schemas and error codes).

## P3 - Operations and Deployment

- [ ] Add Dockerfile and docker-compose for local/prod parity.
- [ ] Add deployment config for target platform (Cloud Run/Render/etc.).
- [ ] Add environment template (`.env.example`) and setup validation checks.
- [ ] Add monitoring/observability (structured logs, metrics, uptime alerts, error tracking).
- [ ] Add backup/restore strategy for Firestore and document storage.
- [ ] Add data export/import capability (project/task/file backups).

## P3 - Documentation and Governance

- [ ] Update README to match actual implemented features vs planned features.
- [ ] Add architecture diagram and data flow docs.
- [ ] Add contributor/developer onboarding guide.
- [ ] Add coding standards and branching/release workflow docs.
- [ ] Add privacy policy, terms, and data retention policy docs.

## Optional Future Enhancements

- [ ] Add recurring project templates by team/department.
- [ ] Add dashboard analytics (velocity, workload balancing, cycle time).
- [ ] Add integrations (Slack/Discord/Email webhooks).
- [ ] Add offline support and progressive web app capabilities.
