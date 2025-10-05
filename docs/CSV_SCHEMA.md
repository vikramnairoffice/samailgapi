# Leads CSV Schema

File: UTF‑8, comma‑separated, header required.

Header
```
email,fname,lname
```

Rules
- `email`: required, non‑empty.
- `fname`, `lname`: optional; when missing, placeholders render empty.
- Extra columns ignored.

Examples
```
email,fname,lname
someone@example.com,Jane,Doe
no-name@example.com,,
```

