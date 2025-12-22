# E2E Test Cases

| ID | Scenario | Steps | Expected Result |
| :--- | :--- | :--- | :--- |
| E2E-001 | Login Flow | 1. Navigate to `/auth/login_page` <br> 2. Check for login button <br> 3. *Note: Cannot fully robot-login Google OAuth reliably without special setup, so we check presence of login UI* | Login page loads with "Googleでログイン" button. |
| E2E-002 | Family Creation | 1. Mock Login (via session injection or specialized dev route if needed, or manual step) <br> *Actually, for E2E in a fenced environment, we might rely on the 'Integration' style bypass or a dev-only backdoor.* <br> For this phase: We will test the **Public/Protected Redirects**. <br> 1. Visit `/family/list` <br> 2. Verify redirect to `/auth/login` | Redirected to login page. |
| E2E-003 | Index Page Layout | 1. Login (Mocked via cookie injection in Playwright) <br> 2. Visit `/` <br> 3. Verify Header, Upload Card, Masonry Grid existence | Components are visible. |

> [!NOTE]
> True E2E with Google OAuth is complex. We will focus on:
>
> 1. Verify Login Page rendering.
> 2. Verify Redirect protection.
> 3. Verify Static Assets loading (CSS check).
