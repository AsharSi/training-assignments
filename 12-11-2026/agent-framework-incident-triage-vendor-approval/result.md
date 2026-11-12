============================================================
MICROSOFT AGENT FRAMEWORK
IT INCIDENT ROUTING SYSTEM
Authentication: Azure Foundry API Key
============================================================

Azure Foundry configuration loaded.
Endpoint: https://ashutosh-foundry.openai.azure.com/openai/v1
Deployment: gpt-5.1

Total incidents loaded: 4

Azure Foundry client initialized.
Graph workflow built successfully.

============================================================
Processing Incident: INC101
Description: The corporate email service is unavailable for every employee across the company.
============================================================

[Triage Agent] Analyzing incident...
[Triage Agent] Severity: HIGH

[Escalation Agent] Handling HIGH-severity incident...

------------------------------------------------------------
FINAL INCIDENT RESPONSE
------------------------------------------------------------

Incident ID: INC101
Severity: HIGH
Assigned Agent: EscalationAgent

1. Incident summary  
- ID: INC101  
- Impact: Company-wide outage of corporate email for all employees.  
- Risk: Business communication halted; potential impact on customers, partners, and critical operations.

2. Responsible support team  
- Primary: Messaging/Collaboration (Email) Support Team  
- Secondary: Network Operations, Identity/Access Management, Security Operations (to rule out attack), Infrastructure/Cloud Ops (depending on email hosting).

3. Immediate containment actions  
- Verify scope: Confirm outage via monitoring tools and user reports; identify affected domains/services (SMTP, IMAP/POP, Webmail, M365/Exchange).  
- Check service health: Review email platform status dashboard, server/cluster health, and cloud provider status pages.  
- Validate core dependencies:  
  - DNS records (MX, Autodiscover, SPF)  
  - Network connectivity to email servers/cloud endpoints  
  - Authentication/SSO services (AD, AAD, IdP)  
- Disable recent risky changes: Roll back or temporarily disable any recent config changes, updates, or deployments related to email, DNS, firewall, or identity.  
- Implement workarounds:  
  - Enable alternative communication channels (Teams/Slack, phone bridges, SMS for critical teams).  
  - For customer-facing teams, provide temporary external email or ticketing alternatives if policy allows.

4. Escalation procedure  
- T+0–15 minutes:  
  - Incident Manager assigned (from IT Operations).  
  - Engage Messaging Support as lead resolver.  
  - Declare HIGH-severity incident in ITSM tool and open bridge line / war room.  
- T+15–30 minutes:  
  - Escalate to: Network Ops, Identity/Access, Infrastructure/Cloud Ops, Security Ops.  
  - If cloud-based (e.g., M365/Google Workspace), open priority support case with vendor and attach logs, correlation IDs, and timeline.  
- T+30–60 minutes:  
  - If no clear root cause, invoke senior engineers and platform architects for email, DNS, and network.  
  - Escalate to IT leadership (CIO/Head of IT) and Business Continuity lead.  
- Ongoing:  
  - Maintain incident log: changes applied, tests performed, decisions, timestamps.  
  - Once service is partially restored, prioritize critical groups (support, finance, execs) and then full rollout.  
- Post-restoration:  
  - Conduct post-incident review: cause, contributing factors, response timeline, corrective actions (monitoring, capacity, change controls, DR/BCP improvements).

5. Communication recommendations  
- Audience: All employees, exec leadership, key business stakeholders, Service Desk.  
- Initial message (within 15 minutes):  
  - Acknowledge company-wide email outage, known impact, and that IT is investigating.  
  - Provide alternative communication methods (e.g., Teams/Slack, phones).  
  - Give next update time (e.g., every 30 minutes).  
- Ongoing updates:  
  - Regular status updates at defined intervals, even if no change.  
  - Separate, more detailed technical updates for leadership and critical departments (support, sales, operations).  
- External communications:  
  - Coordinate with Comms/PR for customer/partner-facing statements if SLAs or support channels are impacted.  
- Resolution notice:  
  - Announce restoration, any required user actions (restart Outlook, re-login, clear cache), and confirm follow-up with root cause summary and prevention steps.
------------------------------------------------------------

============================================================
Processing Incident: INC102
Description: One employee's wireless mouse stopped working.
============================================================

[Triage Agent] Analyzing incident...
[Triage Agent] Severity: LOW

[Resolution Agent] Handling LOW-severity incident...

------------------------------------------------------------
FINAL INCIDENT RESPONSE
------------------------------------------------------------

Incident ID: INC102
Severity: LOW
Assigned Agent: ResolutionAgent

Here are some simple steps the employee can try:

1. **Check the power**
   - Make sure the mouse has power:
     - If it uses batteries, remove and reinsert them, or replace with new batteries.
     - If it’s rechargeable, connect it to the charger for a few minutes, then try again.
   - Confirm any power switch on the mouse is set to ON.

2. **Check the USB receiver (dongle)**
   - Make sure the USB receiver is firmly plugged into the computer.
   - Try unplugging it and plugging it back into a different USB port.
   - Avoid using USB hubs temporarily; plug directly into the computer.

3. **Verify the connection**
   - For wireless with a dongle: Press any “connect” or “pair” button on the mouse if it has one.
   - For Bluetooth mice:
     - On the computer, open Bluetooth settings and check if the mouse appears as connected.
     - If not, remove it from the list of devices and re-pair it.

4. **Test on another device**
   - Plug the USB receiver into another computer (or pair the Bluetooth mouse with another device) to see if it works there.
   - If it works on another device, the issue may be with the original computer’s USB ports or Bluetooth.

5. **Restart and check for interference**
   - Restart the computer.
   - Move the mouse closer to the USB receiver and remove nearby electronic devices that might cause interference (other wireless devices very close to the mouse/receiver).

---

**Escalate to the help desk if:**
- The mouse still does not work after trying all steps above.
- The USB ports or Bluetooth on the computer appear not to work with other devices.
- The mouse is critical for the employee’s work and they need a replacement or further diagnosis.
------------------------------------------------------------

============================================================
Processing Incident: INC103
Description: The company-wide payment processing system is down and transactions are failing.============================================================

[Triage Agent] Analyzing incident...
[Triage Agent] Severity: HIGH

[Escalation Agent] Handling HIGH-severity incident...

------------------------------------------------------------
FINAL INCIDENT RESPONSE
------------------------------------------------------------

Incident ID: INC103
Severity: HIGH
Assigned Agent: EscalationAgent

1. **Incident summary**  
Company-wide payment processing system outage. All transactions are failing, impacting revenue, customer experience, and downstream financial reporting.

2. **Responsible support team**  
- Primary: Payments/Application Support Team  
- Secondary: Infrastructure/Database Team, Network Team, Vendor/PSP Support (if third-party)

3. **Immediate containment actions**  
- Disable new payment attempts on front-end (show maintenance/incident banner).  
- Switch to any available backup payment processor or manual offline processing, where feasible.  
- Collect current logs, error codes, and monitoring data from payment gateway, APIs, DB, and network devices.  
- Confirm scope: internal vs. external users, specific regions, payment types.  
- Freeze non-essential changes to related systems until root cause is identified.

4. **Escalation procedure**  
- Notify on-call leads for Payments Support and Infrastructure immediately via paging system.  
- Escalate to Incident Manager to coordinate response and decision-making.  
- If third-party processor involved, open high-priority ticket and escalate to vendor support.  
- Set defined time thresholds: if not restored within 30 minutes, escalate to IT Director; within 1 hour, escalate to CIO/Business Execs.  
- Initiate formal Major Incident process, including technical bridge call with all relevant teams.

5. **Communication recommendations**  
- Send initial incident notice to impacted business units (Finance, Sales, Customer Support, Operations) with clear impact and workarounds.  
- Update internal status page and collaboration channels at regular intervals (e.g., every 30 minutes) until resolved.  
- Provide customer-facing status updates via status page and support scripts for frontline staff.  
- After resolution, issue an incident report summarizing impact, root cause, timeline, and corrective actions.
------------------------------------------------------------

============================================================
Processing Incident: INC104
Description: One employee cannot print to the nearby office printer.
============================================================

[Triage Agent] Analyzing incident...
[Triage Agent] Severity: LOW

[Resolution Agent] Handling LOW-severity incident...

------------------------------------------------------------
FINAL INCIDENT RESPONSE
------------------------------------------------------------

Incident ID: INC104
Severity: LOW
Assigned Agent: ResolutionAgent

Here are simple steps the employee can follow for issue INC104 (cannot print to nearby office printer):

1. **Check basic connections and power**  
   - Make sure the printer is turned on and shows no error lights/messages on its display.  
   - Confirm it’s properly connected to power and the network (cable firmly plugged in or Wi‑Fi light on, depending on model).

2. **Verify you’re using the correct printer**  
   - When printing, check that the selected printer in the print dialog matches the nearby office printer’s name.  
   - If it’s missing from the list, try closing and reopening the document/app, then check again.

3. **Test from another application**  
   - Try printing a simple test document (e.g., a one-page Word or PDF file).  
   - If the original app won’t print but others do, note which app is failing.

4. **Check your computer’s connection and restart**  
   - Confirm your computer is connected to the office network (wired or Wi‑Fi) and not showing network errors.  
   - Restart your computer and then try to print again.

5. **Ask a nearby coworker to test**  
   - Have a coworker print to the same printer.  
   - Note whether their print job succeeds or fails.

---

**Escalate to the help desk if:**

- The printer does not appear in your printer list after a restart.  
- You see error messages on the printer display (paper jam, offline, out of toner, etc.) that you cannot clear.  
- A coworker also cannot print to the same printer.  
- You have followed all steps and still cannot print, or you receive repeated error messages.------------------------------------------------------------

============================================================
ALL INCIDENTS PROCESSED
============================================================