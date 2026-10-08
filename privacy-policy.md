# Privacy policy: personal WHOOP integration

_Last updated: 2026-10-08_

This is a personal, single-user integration. Its only user is its developer, who
is also the WHOOP member whose data it reads.

**What is accessed.** With the member's authorisation, through the WHOOP API,
using the scopes `read:profile`, `read:body_measurement`, `read:cycles`,
`read:recovery`, `read:sleep` and `read:workout`: the member's own profile, body
measurements, physiological cycles, recovery, sleep and workout records.

**Where it goes.** The data is fetched over HTTPS by software running on the
member's own computer. It is kept there in an encrypted cache for up to 90 days
and then deleted automatically. It is not copied to any server operated by the
developer and is not committed to source control.

**How it is used.** To show the member their own data and trends, and to support
their own wellness and training decisions. It is not used to provide medical
advice.

**AI processing.** If the member has switched it on, short summaries of their own
data are sent to an AI model provider the member has chosen, in order to answer
the member's own questions. If the member has separately switched on access for
an AI agent running on their own computer, that agent can read the same
summaries and passes them to the model provider it uses. Both are off unless
the member turns them on. The integration does not use the data to train or
fine-tune any model.

**Sharing.** The data is not sold, and apart from the AI processing above is
not shared with or transferred to anyone.

**Credentials.** OAuth tokens are stored encrypted on the member's computer. App
credentials are kept in the operating system's credential store.

**Deletion and revocation.** The member can revoke access and delete the cache at
any time from the application.

**Contact.** The email address registered for this app in the WHOOP Developer
Dashboard.
