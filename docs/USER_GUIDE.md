# FireScope AI (Bushfire AI) — User Guide

**Project:** ICT313 Bushfire Risk Application  
**Document:** User Guide  
**Updated:** 19 October 2026  
**Audience:** General users, students, assessors, and demonstration participants

> **Safety notice:** FireScope AI is an educational decision-support prototype. Its AI risk scores are estimates, **not** official Australian Fire Danger Ratings, forecasts of a specific fire, evacuation instructions, or emergency alerts. For immediate danger in Australia, call **000**. Follow official emergency services and local government advice.

## 1. What the application does

FireScope AI brings together location-based bushfire risk estimates, an interactive map, public incident information, climate-related news, and optional account features. The application is designed to help users explore how weather and environmental factors relate to bushfire risk.

The main sections are **Dashboard**, **Risk Map**, **AI Prediction**, **Fire Warnings**, **Climate News**, **Prediction History**, **Saved Locations**, **Settings**, **About**, and **Contact**. Some features require an account; others may be available without signing in.

## 2. Open FireScope AI

1. Open a modern web browser on a desktop, laptop, tablet, or phone.
2. Visit the deployed project: https://2026s2a2.winproject.com.au/
3. Wait for the dashboard to load. An internet connection is required for the hosted application and its live external data services.
4. Use the application's navigation menu to move between sections.

**Note:** The website address reflects the project's deployment at the time this guide was written. Availability can change.

## 3. Dashboard

The Dashboard is the application's starting screen. It provides an overview of bushfire-related information and navigation to the main tools.

1. Open **Dashboard** from the navigation menu.
2. Review the information cards and any available map or risk summaries.
3. Choose **AI Prediction** for a location-specific estimate, **Risk Map** for geographic exploration, or **Fire Warnings** for public incident information.

Dashboard content may change when external data sources update. Do not assume that an empty card means there are no fires or hazards.

## 4. Generate an AI risk prediction

1. Open **AI Prediction**.
2. Follow the on-screen controls to select or enter a location. The interface may support coordinates or a map-assisted location selection, depending on the current version.
3. Submit the prediction request using the button displayed on the page.
4. Allow time for the server to retrieve weather information and run the model.
5. Read the returned **risk score**, **risk category**, and supporting weather information.

### Understanding the result

The deployed model produces a score from **0 to 100** and maps it into these project-defined categories:

| Score | Display category |
|---:|---|
| Below 30 | LOW |
| 30 to below 50 | MODERATE |
| 50 to below 70 | HIGH |
| 70 to 100 | VERY HIGH |

The score comes from a neural-network output transformed onto a percentage-style scale. **It is not a calibrated probability that a fire will occur**, and these labels are **not** the official Australian Fire Danger Rating System categories.

The model considers date/season and weather-derived features such as temperature, humidity, wind, recent rainfall, dryness, and vapour pressure deficit. Predictions depend on the availability and quality of upstream weather data.

### If a prediction fails

- Check that the location information is valid and complete.
- Confirm that your internet connection works.
- Retry after a short delay if a weather provider or the prediction service is temporarily unavailable.
- Do not treat an error or missing prediction as a low-risk result.

## 5. Explore the Risk Map

1. Select **Risk Map** from the navigation.
2. Pan and zoom to the area you want to explore.
3. Select a location using the map controls available in the current interface.
4. Follow the displayed controls to view or compare location information.
5. If signed in, use the provided save option to keep a location for later, where available.

The map uses third-party map tiles. Its appearance and availability depend on the map service and your network connection. Map markers and visual layers are educational aids; they are not authoritative emergency boundaries.

## 6. View Fire Warnings

1. Open **Fire Warnings**.
2. Review the incident cards, categories, and available location details.
3. Use the information to identify reports that may merit further investigation.
4. Confirm any relevant incident directly with the responsible emergency service before acting.

**Source limitation:** The application's incident integration uses a public **NSW Rural Fire Service** feed. It does **not** provide comprehensive incident coverage across Australia, and it should not be interpreted as a complete ACT emergency feed. Information may be delayed, incomplete, unavailable, or cached.

For official warnings, consult the appropriate state or territory emergency service and current local instructions. For immediate danger, call **000**.

## 7. Read Climate News

1. Open **Climate News**.
2. Browse the displayed climate- and environment-related article summaries.
3. Open an article using its displayed link or action, where available.

The news section uses an external publisher feed. Article availability and update timing are outside the project's control. News articles are informational content, not emergency alerts.

## 8. Create an account or sign in

The application supports **email/password** and **Google** authentication through Firebase Authentication.

### Create an email account

1. Open the sign-in or account control in the application header.
2. Choose the account-registration option.
3. Enter the required details and submit the form.
4. Check your email for a verification message, if prompted.
5. Follow the verification instructions provided in the email and application.

### Sign in with email

1. Open the authentication dialog.
2. Choose the sign-in option.
3. Enter your registered email and password.
4. Submit the form.

### Sign in with Google

1. Open the authentication dialog.
2. Select the Google sign-in option.
3. Complete the Google account prompt.

### Forgot your password?

Use the **Forgot password** or password-reset option in the authentication dialog. Enter your account email and follow the instructions sent to that address.

**Privacy tip:** Do not share passwords or verification links. The app does not need your Firebase credentials to provide public incident or news content.

## 9. Prediction History

For signed-in users, the application can store successful predictions in a personal Firestore history collection.

1. Sign in to your account.
2. Generate an AI prediction.
3. Open **Prediction History** from the navigation menu.
4. Review available saved predictions and their recorded values.
5. Use the interface's delete action if you want to remove an entry.

History entries may include location coordinates, a location name, risk score/category, weather summaries, and a creation timestamp. A failed save may not interrupt the prediction itself; therefore, if a result does not appear in History, do not assume it was recorded.

## 10. Saved Locations

1. Sign in to your account.
2. Open **Risk Map** and select a location.
3. Use the on-screen save control when available.
4. Open **Saved Locations** to review saved places.
5. Use the provided controls to revisit or remove a location.

Saved locations may include a custom display name and geographic coordinates. The application attempts to avoid duplicates for near-identical coordinates, but this is not a guarantee against every duplicate.

## 11. Settings and account management

Open **Settings** to access available account-related controls. The implementation includes an email-verification action and a sign-out action. Only use options that are actually visible in your current interface; features such as account deletion or profile editing should not be assumed to exist.

To sign out, use the sign-out control in the header or Settings page. On shared computers, sign out when finished.

## 12. About and Contact

**About** provides project context and purpose. **Contact** provides an interface for sending a message through an external form service. Avoid submitting sensitive personal information, emergency reports, or urgent assistance requests through the project contact form.

For a live bushfire emergency, use official emergency channels instead of the contact form.

## 13. Common problems

| Problem | What to try |
|---|---|
| The website does not load | Check connectivity; retry later; confirm the deployment is online. |
| The map is blank | Check connectivity; refresh; allow map tiles time to load. |
| A prediction fails | Check the selected location; retry when weather/model services recover. |
| Fire incidents do not appear | The NSW feed may be unavailable or outside the area of interest; consult official services. |
| News is missing | The external publisher feed may be temporarily unavailable. |
| Google sign-in fails | Allow the sign-in popup and check browser restrictions. |
| Verification email is missing | Check spam/junk and use the resend option in Settings if available. |
| History does not show a result | Confirm you are signed in and the prediction completed; the Firestore save may have failed. |
| A saved location is missing | Confirm you are using the same signed-in account. |

## 14. Accessibility and responsible use

- Use the application's text labels alongside any colour-based risk indicators.
- On small screens, use the responsive navigation provided by the interface.
- Do not rely on colour, a single score, or a map marker alone to make safety decisions.
- Be aware that some external map and news services may not be fully accessible in every browser.
- Do not use FireScope AI as a substitute for official warnings, local expertise, or an emergency plan.

## 15. Quick demonstration walkthrough

For a short classroom demonstration:

1. Open the **Dashboard** and explain the educational purpose.
2. Open **Risk Map** and select a sample location.
3. Run **AI Prediction** and explain the displayed risk score and categories.
4. Show **Fire Warnings**, clearly identifying the NSW RFS feed as an external source.
5. Show **Climate News** as a separate informational feed.
6. Sign in to demonstrate **Prediction History** and **Saved Locations**, if an appropriate demo account is available.
7. Finish with the safety disclaimer and the distinction between experimental AI estimates and official fire warnings.

## 16. Documentation and support

Technical documentation is maintained in the project's `docs/` directory. The project repository is available at https://github.com/Ayu-gu/bushfire-ai. For implementation details, see `ARCHITECTURE.md`, `MACHINE_LEARNING.md`, `DATABASE_DESIGN.md`, and `TESTING.md`.

**Verification note:** This guide is based on the reviewed navigation and authentication code and previously examined application architecture. Exact button labels, mobile layouts, and some end-to-end user flows should be checked against the deployed interface before final submission. No new end-to-end test is claimed by this document.
