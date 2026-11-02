# Backend API reference

Use `http://localhost:3000` for Docker's same-origin Nginx/API path, or port 5000
for direct local Flask. All request examples are JSON. Errors use
`{"error":"message"}`. All endpoints except health, CSRF, registration and login
require authentication. All modifying requests require `X-CSRF-Token`, including
registration/login. Send cookies on every request and fetch a new token after
login/logout. Passwords and hashes are never returned.

| Method | Path | Request | Successful response |
| --- | --- | --- | --- |
| GET | /api/health | none | `{"status":"ok"}` |
| GET | /api/auth/csrf | none | `{"csrf_token":"..."}` |
| POST | /api/auth/register | `{"email":"alex@example.com","password":"long-password"}` | 201 `{"user":{"id":1,"email":"alex@example.com"}}` |
| POST | /api/auth/login | same credentials | 200 `{"user":{"id":1,"email":"alex@example.com"}}` |
| POST | /api/auth/logout | none | `{"message":"Logged out."}` |
| GET | /api/auth/me | none | `{"user":{"id":1,"email":"alex@example.com"}}` |
| GET | /api/profile | none | `{"profile":{...}}` |
| PATCH | /api/profile | `{"full_name":"Alex","bio":null}` | `{"profile":{...}}` |
| GET | /api/preferences/housing | none | `{"housing":null}` or `{"housing":{...}}` |
| PATCH | /api/preferences/housing | see below | `{"housing":{...}}` |
| GET | /api/preferences/lifestyle/questions | none | `{"questions":[...]}` in display order |
| GET | /api/preferences/lifestyle | none | `{"answers":[]}` or saved answers in display order |
| PUT | /api/preferences/lifestyle/{question_key} | `{"own_answer":"early","roommate_answer":"no_preference","is_requirement":false}` | `{"answer":{...}}` |
| GET | /api/onboarding | none | `{"onboarding":{...}}` |
| POST | /api/onboarding/complete | no body or `{}` | `{"onboarding":{...}}` |

Unspecified success status is 200. API failures: 400 invalid JSON/values, missing
or invalid CSRF, or incomplete onboarding; 401 missing/invalid/expired session or
invalid login; 404 unknown route/question; 405 incorrect method (with Allow
header); 409 duplicate normalized registration email; 415 non-JSON request body;
503 database not ready or a rolled-back preference/profile/completion write.
Onboarding failure also returns the current `onboarding` object.

## Profile and housing partial updates

PATCH preserves omitted fields. Explicit null clears an optional/required answer;
clearing a required answer resets onboarding completion. Invalid updates save
nothing. Unknown fields, user IDs, credentials and timestamps are rejected.

Profile fields: trimmed nonblank full_name (maximum 100 characters) and bio
(maximum 1,000). Both are nullable. The response also includes id, email,
created_at, updated_at and onboarding_completed_at (UTC ISO 8601 or null).

Housing example:

```json
{
  "city": "Seattle",
  "budget_min": "900.00",
  "budget_max": "1500.00",
  "move_in_date": "2027-02-01",
  "lease_months": 12,
  "city_is_requirement": false,
  "budget_is_requirement": true,
  "move_in_is_requirement": false,
  "lease_is_requirement": false
}
```

The response adds updated_at. Budget values are the user's monthly rent share in
USD, accept decimal strings or JSON numbers, and are always returned as strings
with two decimal places or null. Values must be finite, nonnegative, at most
99,999,999.99 and have no fractional cents. Min cannot exceed max, including when
only one bound is patched. City is trimmed/nonblank (100 characters maximum),
move-in must be a real YYYY-MM-DD date, and lease_months must be a positive integer
up to 2,147,483,647. All answer fields can be null.

Flags must be actual Booleans. A true flag needs its corresponding answer; budget
needs at least one bound. Clear a requirement flag together with its last answer.
Validation applies to merged saved/incoming state. Empty PATCH is a no-op for an
existing row; first housing PATCH creates the row. No-op saves retain updated_at.

## Lifestyle replacement and choices

PUT requires **all three** writable fields; omission is not a partial update.
It creates/replaces only that user's row for the selected question. The response
adds question_key and updated_at. Choices are single strings, never arrays or
comma-separated selections. NULL means unanswered or cleared; no_preference
means an explicitly answered roommate preference. It is not an own-answer value.
`is_requirement` applies only to roommate_answer and must be false when that
answer is null or no_preference.

| Key / display order | Own-answer values | Roommate-answer values |
| --- | --- | --- |
| sleep_schedule / 1 | early, late, flexible | same plus no_preference |
| cleanliness / 2 | very_tidy, moderately_tidy, relaxed | same plus no_preference |
| smoking / 3 | non_smoker, smoker | same plus no_preference |
| guests / 4 | rarely, sometimes, often | same plus no_preference |
| pets / 5 | has_pets, no_pets | same plus no_preference |

All five questions are initially required. The questions endpoint supplies the
wording, separate own_answers/roommate_answers lists, display_order and
required_for_onboarding. This is the documented initial questionnaire, not a
final product specification. Definitions are centralized in preferences/questions.py.

## Completion

A complete response looks like:

```json
{
  "onboarding": {
    "completed": true,
    "onboarding_completed_at": "2026-11-01T20:00:00+00:00",
    "eligible": true,
    "missing_fields": [],
    "errors": {}
  }
}
```

Eligibility requires nonblank full_name, every housing answer (including both
budget bounds), and both answers to each required lifestyle question. Bio is
optional. Explicit no_preference counts as answered; null does not. Existing
validation rules still apply. Missing fields use precise paths such as
`housing.city` or `lifestyle.sleep_schedule.roommate_answer`; invalid stored
answers produce field/question-specific errors too. GET never marks completion.
POST validates saved data and sets the timestamp once. Repeated success preserves
it. Valid edits and clearing optional bio retain it; clearing required data resets
it atomically with the edit. Failed updates retain answers and completion state.
Restored answers require explicit completion again. Identity always comes from
the session; clients cannot set completion metadata or select another user.
