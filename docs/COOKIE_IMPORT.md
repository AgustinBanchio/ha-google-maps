# Export Google Maps cookies in Chrome

1. Install [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc), the exporter named in the upstream integration guidance. The exporter is separate from the collector audit.
2. Visit chrome://extensions, open the extension's Details and enable Allow in Incognito.
3. Open a new Incognito window. Visit https://www.google.com/maps and sign into only the existing Google account that receives the shared locations. Check that the intended account is selected.
4. While the Maps tab is active, open Get cookies.txt LOCALLY from Chrome's Extensions menu. Select Netscape as the export format and use Export for the current site's cookies. Save the full exported file locally, outside the repository. Do not use JSON or Export All Cookies.
5. Close the Incognito window without signing out of Google.
6. Run ./tools/Open-CollectorTunnel.ps1 from T3's terminal or desktop PowerShell 7. Keep the Windows desktop logged in and 1Password available; approve its normal SSH key request. The helper uses a temporary limited desktop task and will not ask for the Pi's password.
7. Visit http://127.0.0.1:8787, sign in with the collector admin password from the owner-only private handoff, select the exported file and choose Validate and save session.

Treat the file as a reusable account credential. Never paste it into chat, upload it to a converter or put it in HA configuration/Git. After successful import, delete the temporary export. The collector validates against Google before replacing its encrypted saved session. If rejected, keep the fixed error/status code for troubleshooting and do not share cookie contents.

The accepted file starts with a Netscape/HTTP Cookie File header and contains secure Google-domain session cookies. Do not manually copy a single cookie value or strip the export's attributes.

Primary references: [pinned upstream procedure](https://github.com/pnbruckner/ha-google-maps/blob/b2132123d46c47e5761d5d91cc08ca6b712fe6c1/custom_components/google_maps/cookies.py), [exporter's format documentation](https://github.com/kairi003/Get-cookies.txt-LOCALLY).
