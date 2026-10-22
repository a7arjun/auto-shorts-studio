# Connect the first Bollywood YouTube channel

> Historical setup. The channel now uses the Pokemon pipeline. Follow [Renew YouTube authorization](RENEW_YOUTUBE_AUTH.md) for the current management scope and connection-check workflow.

## Why one channel first
Keep the existing Hollywood setup for later. We will connect one Gmail/YouTube channel before attempting fully automated uploads. The production modern-movie pipeline is **not enabled**: a YouTube API discovery result is not licensed footage.

## One-time OAuth setup

Your Google Cloud project's YouTube Data API v3 is already enabled for discovery.

1. Create your Bollywood YouTube channel, if not already present.
2. Google Cloud Console -> Google Auth Platform -> Clients: Create **Web application** OAuth client. OAuth Playground redirect URI: \`https://developers.google.com/oauthplayground\`.
3. Under Audience, add your Google email as a **test user** if the app is in external Testing status.
4. Open \`https://developers.google.com/oauthplayground/\`. Gear -> *Use your own OAuth credentials* and paste your client's ID/secret in the browser only.
5. Under Step 1, request scope \`https://www.googleapis.com/auth/youtube.upload\`, choose the correct YouTube channel when prompted, and authorize.
6. Under Step 2, exchange the authorization code and securely copy the **refresh token**.
7. Set these GitHub Actions **repository secrets**, not variables:
   - \`YT_HI_CLIENT_ID\`
   - \`YT_HI_CLIENT_SECRET\`
   - \`YT_HI_REFRESH_TOKEN\`
8. From GitHub Actions select \`Bollywood Channel - Private Upload Test\`, Run workflow, and tick \`confirm_private_upload\`. This uploads a self-created 8-second private test-pattern video **once**.
9. Confirm the test video appears as *Private* in the correct channel in YouTube Studio. Never paste secrets into chat or code.

**If the OAuth Playground token was generated before the channel existed, repeat authorization after selecting the intended channel.** If you ever get a \`refresh_token\` exchange without a new token, revoke the specific test app's grant from Google account permissions and authorize again, if appropriate; don't delete the Google Cloud project.

Google External apps in **Testing** expire upload-scope authorizations, including refresh tokens, after approximately 7 days. Publishing status and potential OAuth verification must be handled for a durable, unattended setup.

YouTube's official docs currently conflict about unverified-project *public* upload restrictions, so first verify a private upload and then the project's actual visibility capability.

## After the private test
- Integrate approved modern-movie assets with scene ranking and captions.
- Configure channel-specific upload environment.
- Enable an independent production-only workflow after the source catalogue has rights information and duplicate detection.
- Avoid blindly activating \`AUTOPUBLISH_ENABLED\` in the legacy classic-film pipeline: it is not connected to the modern movie research feed.
