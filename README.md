# POS / POS Referral Onboarding API

FastAPI backend for the digital onboarding flow described in the process
diagrams: link generation by an SM, self-onboarding for POS / POS
Referral, document upload, and an ops approval workflow.

**Exactly 2 database tables** - `users_data` (Table-1) and
`document_details` (Table-2: PAN/Aadhaar/Education extracted fields),
per spec.

**No login/auth is implemented** - this sits behind your existing auth
system. The admin/ops endpoints assume a caller identity (`raised_by`,
`reviewed_by`, etc.) is passed in from whatever your existing auth
middleware resolves.

## How link generation & frontend rendering work

This backend is API-only - it never renders HTML. The "link" is just a
URL that points at a route your **frontend** app owns, carrying an
opaque token as the sole handle back to this API.

1. SM calls `POST /api/v1/links/generate` with `{name, number, user_type, raised_by}`.
2. The backend creates a `users_data` row - `id` is a generated ticket id
   like `TKT-12-09-2026-143059-7` (see "Id format" below), and a random
   token (`secrets.token_urlsafe(32)`, unguessable) is generated and
   embedded into the full onboarding URL, which is stored in
   `onboarding_link` - and returns:
   ```json
   {
     "id": "TKT-12-09-2026-143059-7",
     "token": "9f3c...",
     "onboarding_url": "https://<FRONTEND_BASE_URL>/onboard/pos/9f3c...",
     "share": { "copy_link": "...", "whatsapp": "https://wa.me/...", "sms": "sms:..." }
   }
   ```
3. The SM shares `onboarding_url` (copy link / WhatsApp / SMS) - all three
   are pre-built for you in the response.
4. **The frontend team builds a route matching that shape**, e.g. in React:
   `/onboard/:userType/:token`. When the POS/Referral opens the link:
   - The page reads `token` from the URL.
   - Calls `GET /api/v1/links/{token}` to validate it and fetch prefill
     data (`name`, `number`, `user_type`, `status`).
   - Renders the form based on `user_type`.
   - From then on, every API call in the flow (`onboarding/{token}/form`,
     `onboarding/{token}/documents`, `onboarding/{token}/submit`) is made
     using that same `token` - no login/session needed for the
     POS/Referral side, the token itself is the access credential to
     that one record.
5. If ops sends the record back for corrections
   (`POST /api/v1/admin/onboarding/{id}/review` with `action: SEND_BACK`),
   the backend **rotates the token** and returns a fresh
   `new_onboarding_url`, which you resend to the POS/Referral the same way.

So: this backend never "renders" anything - it is the data/validation
layer behind a frontend route the frontend team controls. `FRONTEND_BASE_URL`
in `.env` is only used to build the shareable link text.

Note: every `{token}` path parameter above is the bare token (as it
appears in the frontend URL), even though `onboarding_link` in the
database stores the full URL - the backend matches records by the
trailing token portion of that stored URL (see
`app/routers/deps.py:get_record_by_token`).

## Project layout

```
app/
  main.py           FastAPI app, router wiring, CORS, static file mount
  config.py         Settings (env vars)
  database.py       SQLAlchemy engine/session
  models/           SQLAlchemy models: users_data, document_details (the only 2 tables)
  schemas/          Pydantic request/response models
  services/         token generation, id generation (TKT-.../DOC-...), storage (local/S3)
  routers/
    links.py        SM: generate link. Frontend: resolve token -> prefill
    onboarding.py    save form, submit
    documents.py     file upload + PAN/Aadhaar/Education structured detail save
    workflow.py      ops: list/review (approve/reject/send-back)
alembic/                    migrations (autogenerate against the models above)
scripts/init_db.py          quick `create_all()` for local dev without migrations
scripts/export_openapi.py   exports the live OpenAPI/Swagger schema to openapi.json
```

## Setup (SQL Server)

Runs against SQL Server via `pymssql` (no ODBC driver install needed -
it bundles FreeTDS).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # edit DATABASE_URL / FRONTEND_BASE_URL as needed
# DATABASE_URL=mssql+pymssql://<user>:<password>@<host>:1433/<database>

# quick start (no migration history):
python -m scripts.init_db

# or, for real migration history:
alembic revision --autogenerate -m "init"
alembic upgrade head

uvicorn app.main:app --reload
```

`scripts/init_db.py` also creates the two SQL Server `SEQUENCE` objects
(`seq_users_data`, `seq_document_details`) the id generator depends on -
run it (or the Alembic migration, once you add one) before starting the
app for the first time against a fresh database.

Docs at `http://localhost:8000/docs`.

This project targets exactly one database - it creates only `users_data`,
`document_details`, and those 2 sequences. If you're pointing
`DATABASE_URL` at a database that already has other tables (e.g. an
existing user-management schema), nothing else in that database is read
or modified.

## Swagger / OpenAPI

FastAPI serves live interactive docs automatically - no extra setup:
- Swagger UI: `<API_PUBLIC_URL>/docs`
- ReDoc: `<API_PUBLIC_URL>/redoc`
- Raw schema: `<API_PUBLIC_URL>/openapi.json`

On the live server (`https://pibspartners.com`) that's
`https://pibspartners.com/docs`.

The `servers` entry in the schema is driven by `API_PUBLIC_URL` in
`.env` (defaults to the URL above) - that's what makes Swagger UI's "Try
it out" send requests to the right host instead of wherever `/docs`
itself is being viewed from. The app is served at the domain root (no
path prefix), so `ROOT_PATH` is left blank; only set it if a reverse
proxy later puts this app behind a stripped path prefix.

A static copy of the schema is checked into the repo as
[openapi.json](openapi.json) (importable into Postman, Swagger Editor,
or handed to another team without them running the app). Regenerate it
after any endpoint/schema change:
```bash
python -m scripts.export_openapi
```

Both tables use a human-readable id instead of a UUID:
`TKT-12-09-2026-143059-7` for `users_data`, `DOC-12-09-2026-143059-4` for
`document_details` - `<PREFIX>-dd-mm-yyyy-HHMMSS-<n>`, where `<n>` comes
from a native SQL Server `SEQUENCE` (see `app/services/id_generator.py`).
Sequences guarantee the trailing number is atomic and gap-safe under
concurrent requests, so two records created in the same second never
collide. The id is generated in application code at insert time (same
pattern as the token embedded in `onboarding_link`) and is immutable
afterward.

## Data model

**`users_data`** (Table-1) - one row per POS / POS Referral: `id`
(ticket id, e.g. `TKT-12-09-2026-143059-7`), `name`, `number`,
`user_type`, `onboarding_link` (the full shareable URL, e.g.
`http://.../onboard/pos/nO5Z-...`), `dob`, `email`, `city`,
`state`, `pincode`, `pan_card`, `educational_qualification`, `aadhaar`,
`photograph`, `cancelled_cheque` (all five as S3/file URLs),
`terms_and_conditions`, `consent`, `raised_by`, `status`, `created_at`,
`updated_at`, `updated_by`, `reviewed_by`, `joining_date`,
`pos_conversion_date`.

`terms_and_conditions` is fixed at creation to
`"we can use your data for onboarding you"` and is **not** part of the
general form-save payload - it has its own endpoint (see below) so it
can be changed independently of everything else on the record.
`reviewed_by` is set automatically to whoever calls the admin review
endpoint (`APPROVE`/`REJECT`/`SEND_BACK`). `joining_date` and
`pos_conversion_date` feed the Ageing Report - see below.

**`document_details`** (Table-2) - one row per `users_data` record
(`id` e.g. `DOC-12-09-2026-143059-4`, `users_data_id` FK), holding
PAN / Aadhaar structured fields extracted from the uploaded documents
(e.g. by an OCR step, or entered manually) plus basic demographic and
bank details: `age`, `pan_number`, `pan_name`, `pan_father_name`,
`pan_dob`, `aadhaar_number`, `aadhaar_name`, `aadhaar_dob`,
`aadhaar_gender`, `aadhaar_address`, `aadhaar_city`, `aadhaar_district`,
`aadhaar_state`, `aadhaar_pincode`, `account_holder_name`,
`account_number`, `ifsc_code`, `bank_name`, `created_at`, `updated_at`,
`updated_by` (full field list in `app/models/documents.py`).

## Endpoints

| Area | Method & Path |
|---|---|
| Link | `POST /api/v1/links/generate` |
| Link | `GET /api/v1/links/{token}` |
| Onboarding | `GET /api/v1/onboarding/{token}` |
| Onboarding | `PUT /api/v1/onboarding/{token}/form` |
| Onboarding | `PUT /api/v1/onboarding/{token}/terms-and-conditions` |
| Onboarding | `POST /api/v1/onboarding/{token}/submit` |
| Documents | `POST /api/v1/onboarding/{token}/documents?doc_type=...` (multipart file) |
| Documents | `PUT /api/v1/onboarding/{token}/documents/pan-details` |
| Documents | `PUT /api/v1/onboarding/{token}/documents/aadhaar-details` |
| Documents | `PUT /api/v1/onboarding/{token}/documents/bank-details` |
| Ops (admin) | `GET /api/v1/admin/onboarding?status=UNDER_REVIEW` |
| Ops (admin) | `POST /api/v1/admin/onboarding/{id}/review` (`APPROVE` / `REJECT` / `SEND_BACK`) |
| Ops (admin) | `POST /api/v1/admin/onboarding/{id}/convert-to-pos` |
| Ops (admin) | `GET /api/v1/admin/users-data` (full `users_data` table, each row joined with its `document_details`) |
| Ops (admin) | `GET /api/v1/admin/users-data/{record_id}` (same join, single record) |
| Ops (admin) | `GET /api/v1/admin/document-details` (full `document_details` table) |
| Ops (admin) | `GET /api/v1/admin/document-details/{document_id}` |
| Reports | `GET /api/v1/admin/reports/ageing` |

## Ageing Report

Tracks how long a POS Referral stays a referral before being promoted
to a full POS: **Date of Joining → POS Referral → POS Conversion Date**.

- `joining_date` is stamped automatically the first time a record's
  status becomes `ACTIVE` (i.e. when ops approves it) - this is "Date of
  Joining" for both POS and POS Referral records.
- Conversion is a manual ops action, not automatic:
  `POST /api/v1/admin/onboarding/{id}/convert-to-pos` (only works on a
  record that is currently `user_type=POS_REFERRAL` and `status=ACTIVE`)
  flips `user_type` to `POS` and stamps `pos_conversion_date`.
- `GET /api/v1/admin/reports/ageing` lists every record that either is
  currently a POS Referral or was converted from one, with:
  `date_of_joining`, `pos_conversion_date` (null if still pending),
  `ageing_days` (days from joining to conversion, or to today if still
  pending), `conversion_status` (`PENDING` / `CONVERTED`), and
  `within_90_days` (whether that ageing is within the 90-day target -
  90 is just a target to measure against, not an enforced cutoff; a
  referral doesn't expire or auto-convert at 90 days).

## Notes / things you'll likely want to swap for production

- **File storage** defaults to local disk (`app/services/storage.py`),
  served back at `/files/...`. Set `STORAGE_BACKEND=s3` + AWS env vars to
  switch to S3 with no route changes.
- **PAN/Aadhaar/Education structured fields** (Table-2) are exposed as
  plain save endpoints - if you add an OCR step later, point it at the
  same `PUT .../pan-details` etc. endpoints.
- **Approval workflow** is a single-step approve here (`UNDER_REVIEW` ->
  `ACTIVE`). There is no audit-history table and no generated POS ID in
  this schema - if you need either later, they'd be additional
  tables/columns beyond the 2-table spec this project currently follows.
- **No link expiry**: `onboarding_link` never expires on its own (no
  `expires_at` column in the spec). A link stops working only when ops
  sends the record back (the token is rotated) or once the record is
  locked (`UNDER_REVIEW` / `APPROVED` / `ACTIVE`).
