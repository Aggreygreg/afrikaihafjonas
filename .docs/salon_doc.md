# Comprehensive Software Design & Specification Document
- **Project:** Hairstyle Booking Platform
- **Version:** 8.0 (Master Document)
- **Status:** Final / Ready for Development
- **Date:** 2025-10-12

---

## Part I: Functional & Non-Functional Specifications (v7.1)

This section contains the complete, finalized requirements defining *what* the system must do.

### 1. Executive summary (what this document is for)
This document defines a lightweight, user-first, multilingual hairstyling booking website for a salon owner (initially one provider). The product lets visitors browse services and providers, book appointments, pay (full/partial), receive confirmation + a QR that adds the appointment to their calendar, and receive reminders by email (or WhatsApp if they opted in). The admin controls everything from a dashboard: services, which providers can perform each service, provider availability, homepage content, business rules (deposit, cancellation), and provider password resets.

**Key principles:**
* Keep the MVP simple and robust (email-only notifications for system reliability).
* Respect privacy laws (GDPR): explicit consent for sharing contacts.
* Make admin tasks easy and allow later extension (provider dashboard, SMS, analytics).

---

### 2. Goals & objectives — detailed explanation
* **For clients (end users):**
    * Ability to discover clear descriptions, images, and video links for hairstyles.
    * Frictionless browsing without sign-in; login only to book.
    * Choose service options (e.g., color, length), select a provider (if >1), pick a time, pay if desired, and get clear confirmation and reminders.
* **For the admin (salon owner):**
    * A single control panel to manage services, providers, availability, bookings, and homepage content (hero image, description, address).
    * Ability to control business rules (deposit amount or percentage, cancellation window, reschedule rules).
    * Full visibility of bookings and payments and the ability to mark offline (cash) payments as complete.
* **For the business:**
    * Build credibility with reviews and professional presentation.
    * Support growth: more providers, branches, and marketing tools later.

---

### 3. User roles & authentication (expanded)
#### 3.1 Roles (clear definitions)
* **Admin** — full system superuser. Can manage everything and reset provider passwords.
* **Service Provider** — represented in the system with a profile (photo, bio, assigned services). In v1 providers are managed entities (no login). Provider receives email notifications with booking & client contact details. (A Provider login/dashboard is a planned v2 feature.)
* **Client (Customer)** — guest or registered user. Guests can browse; registering/logging in becomes required only at the booking confirmation step.

#### 3.2 Authentication & role detection
* Single login page for all users (email + password).
* User model includes role (`admin` | `provider` | `customer`). Emails must be unique across the entire user table to avoid ambiguous role detection.
* On successful login, the server redirects the user to the correct area (admin dashboard or client area). For now providers will not log in, but if a provider role is added later the same role routing will apply.
* Password handling: salted & hashed using a strong algorithm (bcrypt or argon2). Enforce minimum length & complexity.
* Rate limiting & lockout for repeated login failures.
* Session security: secure cookies, httpOnly, SameSite, CSRF protection for forms.

#### 3.3 Password reset & admin reset
* Standard user flow: user clicks "Forgot password" → receives a single-use tokenized reset link via email → sets a new password.
* Admin can also reset provider passwords via the dashboard: either (A) send a reset link to the provider’s email, or (B) generate a secure temporary password (preferable: send link — more secure). Admin actions should be logged in an audit trail.

---

### 4. Multi-language & initial language popup
#### 4.1 UX behavior
* On first visit show a language selection popup/modal with the three options: English (default), Hungarian (Magyar), German (Deutsch).
* The choice is stored locally (cookie/localStorage) and persisted to the user profile if they register.
* All UI strings use an i18n framework and external JSON files so content is editable and new languages can be added later.

#### 4.2 Implementation note
* Keep content keys consistent (e.g., `nav.services`, `hero.title`) to allow translators to update only translation files.
* Admin should be able to edit homepage text for each supported language.

---

### 5. Homepage and navigation (detailed)
#### 5.1 Hero area
* Editable hero background image (admin uploads) — ideally square or landscape optimized for mobile/desktop.
* Editable hero text (title + short description). Use simple rich text or plaintext edited in dashboard.
* "Book Now" CTA that smoothly scrolls to the "Popular Services" preview area. The hero must also include clear address & contact links.

#### 5.2 Menu bar (suggested items)
* Home | Services | Providers | FAQ | About | Contact
* A language switcher and login/sign-up utility should be in the top-right.

#### 5.3 Popular services preview
* Homepage contains a section with 5 most popular/trending services, each with image, name, price, and quick-book link.
* "View More" button leads to full Services Page.

#### 5.4 Footer
* Contact (address, phone), social links (Instagram, TikTok, Facebook), opening hours, privacy & T&Cs, newsletter signup.

---

### 6. Service & provider presentation (media, content, and assignment)
#### 6.1 Service content model
Each service entry includes:
* Title, category, short and full description.
* Price and typical duration.
* Option definitions (color, length, add-ons).
* Images slideshow (admin chooses up to 3 images by default, configurable).
* Video: either an embedded video (hosted) or a button link that opens an external video (TikTok/Instagram/Google Drive). Admin chooses whether a service has an embedded media item or a link. This keeps the site lightweight.

#### 6.2 Provider assignment
* When creating or editing a service, admin must select one or more providers who can perform it.
* During booking, only the providers assigned to that service are shown to the customer. This prevents booking mismatch (not all stylists do every service).

#### 6.3 Provider profiles
* Public page per provider: photo, bio, gallery, services performed, average rating (future), contact method (for provider only — providers won’t be directly emailed unless they are assigned).

---

### 7. Browsing & search
#### 7.1 Guest browsing
* Visitors can navigate all content (services, providers, FAQ) without account creation. This lowers friction and increases conversion rate.

#### 7.2 Search & filters
* Search by service name.
* Filter by category, price range, duration, and provider availability.
* Sorting options — e.g., popularity, price.

---

### 8. Booking flow — full expanded sequence (this is the heart of the product)
The booking flow is intentionally modular and checkpointed so that each step can be validated, tested, and the user can go back to edit choices.

#### 8.1 Steps in detail
1.  **Select service (entry point):** The user clicks "Book/Book Now" on a service detail or service card. The service options page opens. All preconfigured options (color, length, add-ons) are displayed with default prices/affects.
2.  **Pick service options:** Customer selects color, length, and any add-ons. Each option may affect time or price. Show live updated price & duration.
3.  **Choose provider:** If there are multiple providers assigned to this service, show them in a toggle/dropdown. Initially (v1) only one provider is available (the salon owner), so only that provider is selectable. Provider selection is mandatory before scheduling.
4.  **Choose date & time:** Display provider-specific calendar reflecting working hours, booked slots, and admin-blocked dates. The backend checks provider availability atomically before finalizing to prevent race conditions / double-booking.
5.  **Review policies:** Display cancellation window, deposit requirement (amount or %), and reschedule rules that admin configured.
6.  **Authentication checkpoint:** If user is a guest, show a modal prompting them to sign in or sign up. They can also continue the booking after signing up. Their contact preference (WhatsApp or Email) should be captured in registration.
7.  **Payment step:** Options:
    * Pay Full online via Stripe/PayPal.
    * Pay Deposit (configured by admin).
    * Pay Later (cash): booking status set to `Pending Confirmation` and admin alerted.
    * If online, process payment via gateway and listen for webhooks to update payment status.
8.  **Confirmation:** If payment is successful (or Pay Later opted and admin later confirms):
    * Booking is set to `Confirmed`.
    * Email confirmation is sent to customer.
    * Provider receives their notification email (containing all customer contact details the customer consented to share).
    * Booking code and generated QR linking to .ics (or Google Calendar event link) included in email.
9.  **Reminder & post-service flow:**
    * Reminder email on the appointment day (or other configured times).
    * After admin marks booking as `Completed`, a review request email is sent.

#### 8.2 Booking status lifecycle (state machine)
* **Pending:** Booking created but awaiting confirmation (typical for Pay Later).
* **Confirmed:** Slot reserved and customer notified.
* **Completed:** Admin marks after the service has occurred. Triggers review-email.
* **Canceled:** By admin or customer (subject to business rules).
* **No-show:** Optional status if customer failed to attend.

#### 8.3 Edge cases & constraints
* **Double booking prevention:** provider calendar check and DB transaction-level locking.
* **Timezones:** Site uses local salon timezone for display (CET/CEST). If you expect international customers, explicitly display timezone on booking pages.
* **Late changes:** Respect cancellation window; enforce deposit forfeiture if configured.

---

### 9. Payments — architecture & compliance
#### 9.1 Gateways & currencies
* Integrate Stripe (recommended) and PayPal as alternatives; both support EU and multi-currency (EUR, HUF).
* Use official SDK + webhooks for payment confirmation and reconciliation.

#### 9.2 Deposit handling
* Admin can configure deposit rules: fixed amount (e.g., €10) or percentage (e.g., 20%).
* When deposit is required, booking may be confirmed or held depending on business rule (immediate confirm after deposit paid).

#### 9.3 PCI & sensitive data
* Do not store card details on your server. Use Stripe Elements or PayPal hosted pages to remain PCI-compliant.
* Store only minimal transaction identifiers and status. Use tokenization provided by gateway.

---

### 10. Email system & templates (full detail and examples)
All emails should be sent via a transactional email service (SendGrid, Mailgun, or similar) with proper DKIM/SPF to avoid spam.

#### 10.1 Primary events & included fields
* **A. Welcome Email (on sign up):** Short greeting, link to “Book Now”, mention of contact preference options, and note about receiving booking confirmations by email.
* **B. Booking Confirmation (customer):** Includes customer name, booking code, service details, provider name, date & time, salon location, payment status, link to “view booking”, and QR code that links to a downloadable .ics file.
* **C. Provider Notification:** Includes customer full name, email, phone/WhatsApp (if consented), social handles (if provided), service details, booking code, and payment status. A privacy note indicating consent is included.
* **D. Appointment Reminder (customer):** Brief details + link to reschedule/cancel within policy.
* **E. Review Request:** Link to the service-specific review page (tokenized so only verified customers can submit review).
* **F. Password Reset:** Secure, single-use link to reset a password.

#### 10.2 Implementation best-practices
* Use email templates with placeholders.
* Provide unsubscribe/preference controls for marketing emails.
* Log every outgoing email event for audit capability.

---

### 11. Provider notification & privacy (GDPR-safe process)
#### 11.1 Consent capture
* During signup and at checkout, display a clear checkbox (unchecked by default) like: “I consent to share my contact details (phone and social handles) with the provider for appointment coordination.” The consent is stored with the booking record.

#### 11.2 What is shared
* Only share consented data (name, email, phone/WhatsApp, socials, booking notes) to the assigned provider for that booking.

#### 11.3 Logging & deletion
* Admin must be able to export or delete customer data upon request (data subject rights).
* The system stores who viewed or generated provider notifications in audit logs.

---

### 12. Reviews & verification
#### 12.1 Eligibility & display
* Only users who had a confirmed booking and that booking is `Completed` are allowed to post reviews (verified review).
* Provide star rating (1–5) + textual comment.
* Admin moderate queue (auto-publish with optional moderation).

#### 12.2 Display strategy
* Average rating per service shown on service list & provider profile where relevant.
* Select featured reviews for the homepage. Avoid showing unverified reviews.

---

### 13. Admin features — exhaustive
* **13.1 Content management:** Edit hero image & text, salon location, opening hours, social links, and FAQ content per language.
* **13.2 Services management:** CRUD for services, categories. Upload images, choose embed video or external link, set base price & duration, define configurable options & add-ons, mark as “Popular.”
* **13.3 Provider management:** Add/edit provider profile, upload gallery images, assign services they can do. Manage provider availability: weekly schedule plus the ability to block specific dates.
* **13.4 Bookings management:** Filterable list (by date, provider, status). Manual status transitions (confirm, complete, cancel). Mark offline payments complete.
* **13.5 Users & provider password handling:** View user list and reset passwords. Generate secure reset link for providers.
* **13.6 Business rules area:** Configure deposit amount/percentage, cancellation window, forfeiture policy.
* **13.7 Reports & export:** Basic reports (bookings, revenue, top services) and CSV exports.

---

### 14. Data model — highly detailed
See Entity-Relationship Diagram in Part II for the visual schema.
* **User:** id, name, email (unique), password_hash, role (admin|customer), contact_preference (email|whatsapp), socials (json array), language_pref, created_at, updated_at
* **Provider:** id, user_id (nullable), display_name, bio, profile_image_url, availability_rules (JSON), blocked_dates (table)
* **Service:** id, title, category_id, description (i18n), base_price, duration_minutes, images (array), video_embed_url, external_video_link, is_popular flag
* **Booking:** id, user_id, service_id, provider_id, scheduled_start (datetime), scheduled_end, total_price, deposit_amount, payment_status, booking_status (pending|confirmed|etc.), booking_code, share_consent (bool), notes
* **Payment:** id, booking_id, gateway, gateway_txn_id, amount, currency, status
* **Review:** id, booking_id, user_id, rating (1–5), text, approved
* **AuditLog:** id, actor_id, action, target_type, target_id, meta (json)

---

### 15. Non-functional & operational requirements
* **15.1 Security:** HTTPS everywhere, Input validation & sanitization (to prevent SQLi, XSS), CSP headers, bcrypt/argon2 password hashing, Rate limiting, Secrets management, Audit logs.
* **15.2 Privacy / GDPR:** Obtain explicit consent, provide privacy policy, allow data export/deletion requests.
* **15.3 Performance:** Optimize images, lazy load, cache lists, target <= 3 seconds load time.
* **15.4 Backups & monitoring:** Daily automated DB backups, error & uptime monitoring.

---

### 16. Progressive Web App (PWA)
* **16.1 Features included:** Web manifest, service worker for caching, Add-to-home-screen prompt, Offline fallback pages.

---

### 17. Tech stack recommendations
See Selected Technology Stack in Part II for the final decision.
* **Frontend:** React (Create React App / Vite) or Next.js for SEO; Tailwind CSS for quick UI.
* **Backend:** Django (recommended) or Node.js (Express/Nest).
* **Database:** PostgreSQL.
* **Email:** SendGrid or Mailgun.
* **Payments:** Stripe + PayPal.
* **Hosting:** Render / Railway / Heroku for backend; Vercel / Netlify for frontend.
* **CDN & Storage:** Cloudinary for images; AWS S3 for storage.

---

### 18. Developer roadmap & milestones
* **Phase A — MVP (core):** Implement models, public pages, auth, basic booking flow (Pay Later, Stripe test), confirmation emails, and basic admin CRUD.
* **Phase B — Stabilization & polish:** Full payment integration, reminder/review flows, PWA setup, improve admin reports, consent flows.
* **Phase C — Enhancements:** Provider dashboard & login, advanced analytics, Google My Business integration, SMS/WhatsApp integrations.

---

### 19. Testing strategy & acceptance criteria
* **Unit tests:** for business logic (booking validation, availability check).
* **Integration tests:** for payment flow.
* **E2E tests:** for complete booking scenario.
* **Security tests:** attempt typical injection/XSS.
* **Accessibility checks:** (axe or Lighthouse).
* **Acceptance criteria:** booking works end-to-end, admin can manage core entities, emails are triggered, provider notification includes consented data.

---

### 20. Example email templates
* **Booking Confirmation (customer):** Subject: `Your booking is confirmed — [SalonName] — [ServiceName]`. Body: `Hello [Name], your booking for [ServiceName] on [Date] at [Time] with [Provider] is confirmed. Booking code: [CODE]. [View in my account link]. Attached QR/ICS to add to calendar. Payment status: [status]. Contact: [Salon phone].`
* **Provider Notification (provider):** Subject: `New booking assigned — [ServiceName] — [Date]`. Body: `Hello [ProviderName], a new booking has been assigned. Customer: [Name]. Email: [email]. Phone/WhatsApp: [phone — only if customer consents]. Service: [options]. Time: [Date/time]. Booking code: [code]. Notes: [text]. This customer consented to share contact info with you for coordination.`

---

### 21. Final legal & compliance notes
* Display Privacy Policy & Terms during signup; have explicit checkboxes for consent.
* Have data processing agreements (DPA) in place for third-party services.
* Implement GDPR-ready flows: data export and deletion from admin UI.

---

### 22. Deliverables
* This specification document (v7.1 base).
* Translation key files skeleton (JSON).
* Sample content and credentials for staging.

---

### 23. Next suggestions I recommend
* Start with a Django backend + Django admin for MVP. Use React for the frontend if you want modern interactivity and PWA features.
* Keep the first release focused. Add provider login later.

---

### 24. Closing notes
This document integrates all requirements: language popup, editable hero, guest browsing, detailed booking flow, provider assignment, email notifications with consent, QR calendar linkage, PWA readiness, and full admin controls.

---
---

## Part II: System Design & Technology Stack

This section details *how* the system will be built, including the chosen technology and the database schema.

### 25. Selected Technology Stack
Given the project requirements and the developer's existing expertise in Python, the following technology stack has been selected to ensure rapid development, maintainability, and performance. This is a **Pragmatic Django Powerhouse** stack.

* **Backend Framework: Django**
    * **Rationale:** Django's "batteries-included" nature is a massive accelerator. The built-in Admin Panel will create the bulk of the required admin dashboard with minimal effort. Its robust ORM and security features make it a reliable and secure choice.

* **Frontend Approach: Django Templates + HTMX**
    * **Rationale:** To leverage the developer's existing Django skills and avoid the steep learning curve of a full JavaScript framework like React, the frontend will be rendered by Django's templating engine. **HTMX** will be used to provide modern, dynamic user experiences (like updating parts of a page without a full reload) without writing complex JavaScript, dramatically speeding up development.

* **Database: PostgreSQL**
    * **Rationale:** As the industry standard for professional Django projects, PostgreSQL offers robustness, scalability, and advanced features that will support the application's growth.

* **Styling: Tailwind CSS**
    * **Rationale:** A utility-first CSS framework that allows for rapid development of modern, custom user interfaces directly within the HTML templates.

### 26. System Architecture Overview
The system uses a **Pragmatic Monolithic Architecture**. The entire application is a single, unified Django project, which is efficient and simple to develop, deploy, and maintain.