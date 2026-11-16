# Nyarutarama Tennis Club — Django Backend

REST API backend for the Nyarutarama Tennis Club frontend.  
Auth: session cookies (no JWT). CORS is pre-configured for `localhost:5173`.

---

## Quick start

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations  (creates db.sqlite3)
python manage.py migrate

# 3. Seed the three courts + demo accounts
python manage.py seed_demo

# 4. Start the dev server
python manage.py runserver
```

The server runs on **http://localhost:8000** — matching the frontend's `VITE_API_URL`.

---

## Demo accounts

| Email | Password | Role |
|---|---|---|
| manager@nyarutarama.rw | manager123 | OPERATIONS_MANAGER |
| alice@example.com | customer123 | CUSTOMER (regular) |
| vip@example.com | customer123 | CUSTOMER (VIP) |

---

## API reference

### Auth — `/api/auth/`

| Method | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Register (always CUSTOMER role) |
| POST | `/api/auth/login/` | Public | Login, sets session cookie |
| POST | `/api/auth/logout/` | ✓ | Clears session |
| GET | `/api/auth/me/` | ✓ | Current user info |

**Register body:** `{ full_name, email, phone, password }`  
**Login body:** `{ email, password }`  
**Me response:** `{ full_name, role, is_vip, email, phone }`

---

### Bookings (customer) — `/api/bookings/`

| Method | URL | Description |
|---|---|---|
| GET | `/api/bookings/availability/?date=YYYY-MM-DD` | All confirmed bookings for the day |
| POST | `/api/bookings/` | Create a booking |
| POST | `/api/bookings/{id}/cancel/` | Cancel own booking |

**Create body:** `{ court: 1-3, date: "YYYY-MM-DD", start_time: "HH:00" }`  
**Availability response item:** `{ id, court, start_time: "HH:MM", is_mine: bool }`

---

### Manager — `/api/bookings/manager/`

All endpoints require `role == OPERATIONS_MANAGER`.

| Method | URL | Description |
|---|---|---|
| GET | `/api/bookings/manager/` | All bookings (supports `?date=`, `?court=`, `?status=`) |
| POST | `/api/bookings/manager/` | Create booking on behalf of a customer |
| POST | `/api/bookings/manager/{id}/cancel/` | Cancel any confirmed booking |
| GET | `/api/bookings/manager/customers/` | List all customers & coaches |
| POST | `/api/bookings/manager/customers/{id}/vip/` | Toggle VIP status |
| GET | `/api/bookings/manager/coaches/` | List coaches |
| POST | `/api/bookings/manager/coaches/` | Create coach account (sends invite email) |
| POST | `/api/bookings/manager/coaches/{id}/toggle/` | Activate / deactivate coach |

**Manager create booking body:** `{ customer_id, court, date, start_time }`  
**Manager cancel body:** `{ reason: "maintenance|schedule_change|customer_request|other", note?: "" }`

---

### Notifications — `/api/notifications/`

| Method | URL | Description |
|---|---|---|
| GET | `/api/notifications/` | Current user's notifications |
| POST | `/api/notifications/{id}/read/` | Mark one as read |
| POST | `/api/notifications/mark-all-read/` | Mark all as read |

**Notification item:** `{ id, type, is_read, created_at, data }`  
**Types:** `booking_confirmed`, `booking_cancelled`, `booking_cancelled_by_staff`, `vip_assigned`, `vip_removed`

---

## CSRF

The frontend must include the `X-CSRFToken` header on every mutating request (`POST`/`PUT`/`DELETE`).  
The browser receives the `csrftoken` cookie on the first request. The frontend's `request()` function in
`authService.js` should read it and attach the header. Update `authService.js` like this:

```js
function getCookie(name) {
  return document.cookie.split('; ').find(r => r.startsWith(name + '='))?.split('=')[1] ?? ''
}

// Inside the fetch() call, add:
headers: {
  'Content-Type': 'application/json',
  'X-CSRFToken': getCookie('csrftoken'),
},
```

---

## Environment variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | (insecure placeholder) | Django secret key |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated frontend origins |
| `EMAIL_BACKEND` | console (prints to terminal) | Set to SMTP in production |

---

## Production checklist

- Change `SECRET_KEY` to a long random string
- Set `DEBUG=False`
- Configure a real database (PostgreSQL recommended)
- Configure SMTP email
- Collect static files: `python manage.py collectstatic`
- Set `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` (requires HTTPS)
