# Rules of Engagement

The ROE is a signed, machine-readable restriction document. It cannot broaden the Engagement scope.

## Required fields

- engagement and ROE identifiers;
- validity window and authorized test window;
- target IDs and test-case IDs;
- action classes and approval requirements;
- rate, concurrency, data, time, token, and tool-call limits;
- expected network destination profiles;
- stop conditions and emergency contacts;
- evidence handling and retention class;
- cleanup/reset requirements;
- prohibited actions;
- signature and policy version.

## Required process

1. Author drafts Engagement and ROE.
2. Schema and semantic validation run.
3. Security reviewer checks boundaries, target ownership, and data classification.
4. Authorized approver signs.
5. Scope service publishes immutable version and digest.
6. Jobs reference the exact version/digest.
7. Any change creates a new version and invalidates pending grants.

## Mandatory prohibitions

- public/third-party target access;
- internet-scale discovery;
- production exploit execution;
- credential dumping;
- persistence, stealth, or log deletion;
- data exfiltration;
- denial of service;
- social engineering;
- autonomous merge/deployment/patch application.
