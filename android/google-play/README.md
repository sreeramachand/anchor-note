# Google Play Store metadata & guidance (Anchor Note)

This folder holds metadata and assets you need to prepare for Play Store listing.

## Recommended structure
- `changelogs/` — per-version release notes
- `screenshots/` — phone/tablet screenshots (PNG)
- `store_listing/` — longer descriptions, promo text, etc.

## Steps to publish
1. Build an AAB with Buildozer: `buildozer -v android release` (configure keystore).
2. Test the AAB on internal test track before wider rollout.
3. Prepare store listing assets:
   - High-res icon: 512x512 PNG
   - Feature graphic (1024x500)
   - Screenshots: phone (at least 2-4, recommended portrait)
4. Create a privacy policy page and provide the URL in Play Console.
5. Upload AAB, fill in store listing, content rating, target audience, and complete the questionnaire.
6. Submit and monitor pre-launch reports.

## Notes about permissions & background behavior
- If your app uses alarms that wake the device, declare that behavior clearly in the store listing and add an appropriate privacy/security policy.
- Use a foreground service for persistent reminders (Android 8+ restrictions). Buildozer / Python-for-Android supports creating a foreground service via a custom Java/Kotlin module or by using Plyer + BroadcastReceivers; this requires extra work and testing.

