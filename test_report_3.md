# Test Report 3: Frontend-Backend Integration & Authentication Fixes

This report documents the errors encountered during the frontend and backend integration test, specifically during the Seller and Buyer authentication flow, along with their root causes and solutions.

---

## Error 1: Port Mismatch (`ERR_CONNECTION_REFUSED`)
- **Symptom:** Attempting to access the frontend via `http://localhost:3000` resulted in a browser `ERR_CONNECTION_REFUSED` error.
- **Root Cause:** The `README.md` falsely documented that the frontend Vite server would start on port `3000`. The Vite server actually spun up on `http://localhost:8080`.
- **Solution:** 
  - Navigated to `http://localhost:8080` instead.
  - Updated the `README.md` to correctly reflect the `8080` port to prevent future confusion.

## Error 2: API Network Error / "Invalid Email" Block
- **Symptom:** When submitting the signup form with a correct email, the UI failed and displayed: `Network error - is the Django backend reachable?`
- **Root Cause:** 
  - The backend `.env` file was mistakenly set to `DEBUG=False`, which enables production-grade security including `SECURE_SSL_REDIRECT = True`.
  - When the frontend attempted to `POST` to the backend via HTTP, the backend responded with a `301 Redirect` to HTTPS.
  - The browser's CORS policy immediately blocked the redirect, causing a hard network failure on the frontend.
  - Furthermore, `http://localhost:8080` was not listed in the backend's `CORS_ALLOWED_ORIGINS`.
- **Solution:** 
  - Modified the backend `.env` file to set `DEBUG=True`.
  - Added `http://localhost:8080` to `CORS_ALLOWED_ORIGINS`.
  - Restarted the Django server to load the new environment variables, instantly allowing API communication.

## Error 3: Seller Commission Checkbox Validation Bug
- **Symptom:** During Seller Registration, checking the "I accept the Commission Policy" checkbox still resulted in a validation error: `"You must accept the commission policy"`, completely blocking the user from signing up.
- **Root Cause:** The `shadcn/ui` custom `<Checkbox />` component in `SignupPage.tsx` was not correctly integrating its internal boolean state with React Hook Form's `register` function. The Zod schema therefore thought the field was always `undefined` or `false`.
- **Solution:** 
  - As requested by the user, the checkbox requirement was entirely removed to streamline signups.
  - Removed `commissionAccepted` from the Zod validation `sellerSchema`.
  - Deleted the checkbox and its label JSX from `SignupPage.tsx`.

---
**Status:** All integration blockers resolved. Authentication flow is functioning smoothly.
