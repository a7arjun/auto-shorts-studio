# Enable the separate app information site

The static homepage, privacy policy and terms are in this automation repository's `docs` folder. They do not edit or link to the operator's portfolio. They use the public project support link and contain no personal email addresses, credentials, login, scripts or analytics. GitHub Pages remains subject to its own hosting terms and technical logging.

1. Open https://github.com/a7arjun/auto-shorts-studio/settings/pages .
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Under **Branch**, choose **main** and **/docs**, then **Save**.
4. Wait for the Pages build to complete. Use the exact **Visit site** URL returned by GitHub. The expected default is `https://a7arjun.github.io/auto-shorts-studio/`; an existing account-level custom domain could change this, so confirm the actual URL before using it in Google.
5. Confirm the homepage, `privacy.html` and `terms.html` open publicly without a login.
6. Google Auth Platform → Branding: use app name **Battle Logic Lab Publisher**; put the actual live homepage and its privacy/terms URLs in the corresponding fields. For the default GitHub URL, the authorized domain is **a7arjun.github.io**, with no scheme, slash or repository path. If GitHub returns another host, use the appropriate domain you control rather than this expected value.
7. Save, then return to Audience and check whether **Publish app** is available. Do not claim production status until Google confirms it.

If Google asks for domain ownership verification, inspect its exact requirement. Search Console supports URL-prefix HTML verification, but a project-path property is not automatically proof of ownership of an entire authorized domain. A custom domain or control of the GitHub user-site root may be needed depending on Google's requirement. Do not modify the portfolio or add an unrelated domain to get around verification. Do not promise that free hosting alone guarantees OAuth approval.

After publication, follow [Renew YouTube authorization](RENEW_YOUTUBE_AUTH.md) to generate a new refresh token and run a non-uploading connection probe.
