# Setup Checklist

## Required Credentials

- Gemini API key
- SerpAPI key
- Google OAuth client ID / secret / refresh token
- Google Search Console site property identifier (`GSC_SITE_URL`)
- Google Analytics 4 property ID (`GA4_PROPERTY_ID`)

## Later / optional credentials

- Google Ads developer token
- Google Ads customer ID

## Phase 2 Google values

Add these to your local `.env`:

```env
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REFRESH_TOKEN=
GSC_SITE_URL=sc-domain:danilulmashev.com
GA4_PROPERTY_ID=
```

Notes:

- `GSC_SITE_URL` for a verified domain property should use the API identifier form, for example `sc-domain:danilulmashev.com`.
- `GA4_PROPERTY_ID` must be the numeric GA4 property ID, not the `G-...` measurement ID.

## Content Inputs

- Portfolio root URL
- Existing blog post URLs
- Initial seed keywords for restaurant SaaS and restaurant technology

## Local Defaults

- Default geography: Montreal / Quebec / Canada
- Default language flow: French first, English second
