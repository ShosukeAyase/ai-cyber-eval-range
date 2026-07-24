# Project Source Review

All uploaded project files were inventoried. Text was extracted and searched for architecture, authorization, assessment, network, IAM, evidence, isolation, incident-response, and cleanup concepts. Sources were weighted by authority and relevance rather than treated as equally reliable.

| Source | Use in this design | Reliability/limitations |
|---|---|---|
| `AGENTS.md` | Binding repository invariants, workflow, validation, and completion report | Primary project instruction; highest local precedence |
| `(ISC)² CISSP CBK Reference` | Security architecture, risk, IAM, assessment authorization, evidence, logging, cleanup | Authoritative certification reference; older than current standards in some product details |
| `(ISC)² CISSP Official Study Guide` | Secure design principles, white/gray-box testing, BAS, vulnerability workflow, logging | Authoritative exam guide; concepts used, product examples not treated as current recommendations |
| `(ISC)² CISSP Official Practice Tests` | Cross-check of management approval, accountability, egress filtering, regression testing | Educational validation source; questions are not normative controls |
| `TCP/IP Illustrated, Volume 1` | Protocol behavior, firewall/NAT, routing, DNS, TCP/UDP, packet evidence | Strong technical reference; protocol fundamentals remain useful, operational examples may be dated |
| `TCP/IP Illustrated, Volume 2` | Host networking implementation, sockets, routing, packet-processing context | Deep implementation reference; historical BSD implementation details are not direct deployment requirements |
| `TCP/IP Illustrated, Volume 3` | Client/server concurrency, tunneling, application gateways, RPC/NFS concepts | PDF text layer is largely unreadable; selected chapter openings for tunneling and application-level gateways were OCR-checked. It was used only for topic orientation, not as a normative basis |
| Duane C. Wilson, *Cybersecurity* (MIT Press) | Defense in depth, separation, firewall/IDS/IPS/SIEM overview | Peer-reviewed academic press overview; concise rather than implementation-specific |
| Gupta & Goyal, *Cybersecurity: A Self-Teaching Introduction* | Secure design principles, risk monitoring, security architecture | Academic instructional source; some terminology and examples are broad or dated |
| HBR, *Cybersecurity* | Governance and shared executive responsibility context | Management-oriented secondary source; not used for technical controls |
| Shane & Hunker, *Shared Risks, Shared Responsibilities* | Governance, public/private responsibility, policy tradeoffs | Academic/legal policy collection; not used for technical implementation claims |
| *Cybersecurity: An Ultimate Guide...* | Indexed for completeness | Low-authority popular source; excluded from substantive design decisions |

## Source precedence used

1. Project invariants in `AGENTS.md`.
2. Current primary standards and official system documentation in `docs/references.md`.
3. Authoritative CISSP and technical references.
4. Academic and management context.
5. Low-authority sources only for completeness, not for decisions.
