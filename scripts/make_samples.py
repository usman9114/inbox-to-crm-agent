"""Builds sample_data/emails.jsonl and eval/labels.csv from one ground-truth table.

Everything here is fictional: made-up companies, example.com addresses and
555-01xx phone numbers. Labels are written alongside the email text so the
ground truth never depends on what a model says.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["company", "contact_name", "email", "phone", "budget", "timeline", "product_interest"]

# (id, intent, urgency, from, subject, body, labels dict)
E = []


def add(id_, intent, urgency, sender, subject, body, **labels):
    E.append(dict(id=id_, intent=intent, urgency=urgency, **{"from": sender}, subject=subject,
                  body=body.strip(), labels=labels))


# ---------------- sales leads (20) ----------------
add("e001", "sales_lead", 5, "maria.ortega@harborline-logistics.example.com",
    "Need field scheduling software live before Q1",
    """Hi team,

I'm Maria Ortega, operations director at Harborline Logistics. We run 140 drivers and
our dispatch is still on spreadsheets. We want your Field Service Scheduling product
and we have budget approved: around $45,000 for year one. We need it live within 6 weeks
because our peak season starts on January 5th. Can someone call me today? 555-0142.

Maria""",
    company="Harborline Logistics", contact_name="Maria Ortega", email="maria.ortega@harborline-logistics.example.com",
    phone="555-0142", budget="$45,000", timeline="within 6 weeks", product_interest="Field Service Scheduling")

add("e002", "sales_lead", 3, "d.okafor@piedmontdental.example.com",
    "Pricing question",
    """Hello,

We are a 4-location dental group (Piedmont Dental Partners). Looking at your Inventory Sync
tool for supplies tracking across clinics. No fixed budget yet, we first need to see pricing.
Hoping to decide sometime next quarter. Please send a quote.

Thanks,
Dr. Daniel Okafor""",
    company="Piedmont Dental Partners", contact_name="Daniel Okafor", email="d.okafor@piedmontdental.example.com",
    phone="", budget="", timeline="next quarter", product_interest="Inventory Sync")

add("e003", "sales_lead", 4, "priya@lumenfold-studio.example.com",
    "Demo request - analytics dashboard",
    """Hi,

Priya Raman here from Lumenfold Studio, a small design agency (12 people). We'd like a demo of the
Analytics Dashboard this week if possible. Budget is roughly $500 per month. We're switching from
a competitor whose contract ends on the 30th so it's fairly urgent.

My direct line is 555-0187.""",
    company="Lumenfold Studio", contact_name="Priya Raman", email="priya@lumenfold-studio.example.com",
    phone="555-0187", budget="$500 per month", timeline="before the 30th", product_interest="Analytics Dashboard")

add("e004", "sales_lead", 2, "t.nakamura@ridgeway-farms.example.com",
    "Exploring options for 2027",
    """Good afternoon,

I manage IT for Ridgeway Farms Cooperative. We're just starting to look at tools for tracking
equipment maintenance and may budget for it in the 2027 cycle. Nothing urgent. Could you send some
product information about Field Service Scheduling? 

Regards,
Takeshi Nakamura""",
    company="Ridgeway Farms Cooperative", contact_name="Takeshi Nakamura", email="t.nakamura@ridgeway-farms.example.com",
    phone="", budget="", timeline="2027 budget cycle", product_interest="Field Service Scheduling")

add("e005", "sales_lead", 5, "cfo@quillandcrate.example.com",
    "URGENT: replace our support desk this month",
    """To whom it may concern,

Our current help desk vendor is shutting down on the 15th. Quill & Crate (e-commerce, ~30k orders a month)
needs a Support Desk replacement running before then. Budget up to $2,000/month. I'm Sophie Laurent, CFO.
Phone: 555-0123. Please reply ASAP.""",
    company="Quill & Crate", contact_name="Sophie Laurent", email="cfo@quillandcrate.example.com",
    phone="555-0123", budget="up to $2,000/month", timeline="before the 15th", product_interest="Support Desk")

add("e006", "sales_lead", 3, "info@bluepeak-hvac.example.com",
    "Quote for scheduling software",
    """Hi, we're Bluepeak HVAC Services, 22 technicians. We heard about your scheduling product from a
trade show. What does it cost for a team our size? We'd want to start in about 3 months.
Contact me at 555-0156. Carlos Mendes.""",
    company="Bluepeak HVAC Services", contact_name="Carlos Mendes", email="info@bluepeak-hvac.example.com",
    phone="555-0156", budget="", timeline="in about 3 months", product_interest="scheduling software")

add("e007", "sales_lead", 4, "anneli.virtanen@northfjord-media.example.com",
    "Enterprise licence enquiry",
    """Hello,

I'm Anneli Virtanen, head of data at Northfjord Media. We have 300 staff and want to roll the Analytics
Dashboard out company-wide. Our budget for this is $80k-$100k annually. Procurement wants a decision by
end of this month. Can we set up a call with your enterprise team?""",
    company="Northfjord Media", contact_name="Anneli Virtanen", email="anneli.virtanen@northfjord-media.example.com",
    phone="", budget="$80k-$100k annually", timeline="decision by end of this month", product_interest="Analytics Dashboard")

add("e008", "sales_lead", 1, "hello@sundial-bakery.example.com",
    "just curious",
    """hi! we are a tiny bakery (me and two staff). saw your site. probably too big for us but is there
anything for a very small shop? no budget really, maybe next year. - Jo""",
    company="Sundial Bakery", contact_name="Jo", email="hello@sundial-bakery.example.com",
    phone="", budget="", timeline="maybe next year", product_interest="")

add("e009", "sales_lead", 5, "r.castellanos@vertexbuild.example.com",
    "Inventory sync across 9 warehouses, need to start this week",
    """Hi,

Rafael Castellanos, VP Operations at Vertex Build Supply. We lost our inventory system in a migration
failure and need Inventory Sync for 9 warehouses running within 10 days. Budget is not a constraint,
we have signed off up to $120,000. Call 555-0164 or reply here.""",
    company="Vertex Build Supply", contact_name="Rafael Castellanos", email="r.castellanos@vertexbuild.example.com",
    phone="555-0164", budget="up to $120,000", timeline="within 10 days", product_interest="Inventory Sync")

add("e010", "sales_lead", 3, "lena.fischer@oakhollow-clinic.example.com",
    "Partnership / reseller question",
    """Hello,

Lena Fischer, Oak Hollow Veterinary Clinic. We'd like to know whether you offer a reseller or partner
programme. We advise about 15 small clinics on software. No set budget, we'd earn commission if so.
Timeline is flexible, we are planning for spring.""",
    company="Oak Hollow Veterinary Clinic", contact_name="Lena Fischer", email="lena.fischer@oakhollow-clinic.example.com",
    phone="", budget="", timeline="spring", product_interest="reseller programme")

add("e011", "sales_lead", 4, "samir@tidewater-boats.example.com",
    "Re: your brochure",
    """Samir Haddad from Tidewater Boat Rentals. I got your brochure. We need to track 60 boats and
bookings. We can spend about $12,000 and want it working before the May season opens. Can you do a
demo of the Field Service Scheduling module next week? 555-0191""",
    company="Tidewater Boat Rentals", contact_name="Samir Haddad", email="samir@tidewater-boats.example.com",
    phone="555-0191", budget="$12,000", timeline="before May", product_interest="Field Service Scheduling")

add("e012", "sales_lead", 2, "accounts@greenleaf-print.example.com",
    "Information request",
    """Please send information about your dashboard product. Greenleaf Print Works.
Thank you.
- Hannah Weiss""",
    company="Greenleaf Print Works", contact_name="Hannah Weiss", email="accounts@greenleaf-print.example.com",
    phone="", budget="", timeline="", product_interest="dashboard product")

add("e013", "sales_lead", 5, "ceo@solstice-solar.example.com",
    "Need Support Desk + Analytics bundle, board meets Friday",
    """Hi team,

Isabela Cruz, CEO of Solstice Solar Installers. Our board meets this Friday and I want to present a
plan for Support Desk plus the Analytics Dashboard. We have $30,000 earmarked. Please send pricing
today and book me a call tomorrow morning. 555-0178.""",
    company="Solstice Solar Installers", contact_name="Isabela Cruz", email="ceo@solstice-solar.example.com",
    phone="555-0178", budget="$30,000", timeline="board meets this Friday", product_interest="Support Desk and Analytics Dashboard")

add("e014", "sales_lead", 3, "m.brandt@kestrel-law.example.com",
    "Do you support SSO?",
    """Hello, Martin Brandt, IT lead at Kestrel Legal LLP. Before we consider buying Support Desk for our
50-person firm, we need to confirm SSO (SAML) support and where data is hosted. If it checks out we'd
purchase this quarter, around $6,000 per year.""",
    company="Kestrel Legal LLP", contact_name="Martin Brandt", email="m.brandt@kestrel-law.example.com",
    phone="", budget="around $6,000 per year", timeline="this quarter", product_interest="Support Desk")

add("e015", "sales_lead", 4, "yuki.tanaka@mosaic-retail.example.com",
    "Retail chain, 40 stores, looking for Inventory Sync",
    """Hi,

Yuki Tanaka, Mosaic Retail Group. 40 stores, each with its own stock sheet. We want to pilot Inventory
Sync in 3 stores starting next month and expand if it works. Pilot budget about $8,000. Phone 555-0135.""",
    company="Mosaic Retail Group", contact_name="Yuki Tanaka", email="yuki.tanaka@mosaic-retail.example.com",
    phone="555-0135", budget="$8,000", timeline="pilot starting next month", product_interest="Inventory Sync")

add("e016", "sales_lead", 2, "owner@fernwood-cafe.example.com",
    "Question about plans",
    """Hello. I own Fernwood Cafe (3 sites). Are there monthly plans under $100? I would like to try
the Analytics Dashboard to see which items sell. In no rush. Regards, Elena Petrova""",
    company="Fernwood Cafe", contact_name="Elena Petrova", email="owner@fernwood-cafe.example.com",
    phone="", budget="under $100 per month", timeline="no rush", product_interest="Analytics Dashboard")

add("e017", "sales_lead", 5, "b.adeyemi@crestline-airfreight.example.com",
    "Dispatch outage - need a replacement scheduling system immediately",
    """Our dispatch tool failed and we have trucks idle. Bola Adeyemi, COO of Crestline Air Freight.
We will pay for emergency onboarding. Budget: $60,000. We need Field Service Scheduling live in 7 days.
Call now: 555-0149.""",
    company="Crestline Air Freight", contact_name="Bola Adeyemi", email="b.adeyemi@crestline-airfreight.example.com",
    phone="555-0149", budget="$60,000", timeline="in 7 days", product_interest="Field Service Scheduling")

add("e018", "sales_lead", 3, "contact@juniper-edu.example.com",
    "Nonprofit discount?",
    """Hi, Juniper Learning Foundation is a registered nonprofit. We want Support Desk for our
student helpline. Do you offer nonprofit pricing? Our budget is about $3,000 for the year and we
want to launch at the start of the school term in September. - Tomas Novak""",
    company="Juniper Learning Foundation", contact_name="Tomas Novak", email="contact@juniper-edu.example.com",
    phone="", budget="about $3,000 for the year", timeline="start of school term in September", product_interest="Support Desk")

add("e019", "sales_lead", 4, "a.kowalczyk@brightpath-staffing.example.com",
    "Trial for our recruiters",
    """Anna Kowalczyk, Brightpath Staffing. We have 25 recruiters and want to trial the Analytics Dashboard
for two weeks, then buy if the numbers look good (budget $15,000 a year). We'd like to begin the trial Monday.
Reach me on 555-0113.""",
    company="Brightpath Staffing", contact_name="Anna Kowalczyk", email="a.kowalczyk@brightpath-staffing.example.com",
    phone="555-0113", budget="$15,000 a year", timeline="trial starting Monday", product_interest="Analytics Dashboard")

add("e020", "sales_lead", 3, "sales.inquiry@delmar-hotels.example.com",
    "Multi-property rollout",
    """We operate 6 boutique hotels (Delmar Hotels). Interested in Support Desk for guest requests
across properties. Budget TBD. Our general manager Ines Duarte will decide after seeing a demo, probably
within two months.""",
    company="Delmar Hotels", contact_name="Ines Duarte", email="sales.inquiry@delmar-hotels.example.com",
    phone="", budget="", timeline="within two months", product_interest="Support Desk")

# ---------------- support (10) ----------------
add("e021", "support", 4, "jon.pike@harborline-logistics.example.com",
    "Dashboard not loading since this morning",
    """Hi support, the Analytics Dashboard has shown a blank page since 8am for all of our users.
Console says 500 error from /api/reports. This is blocking our weekly review. Account: Harborline Logistics.
- Jon Pike""",
    company="Harborline Logistics", contact_name="Jon Pike", email="jon.pike@harborline-logistics.example.com",
    phone="", budget="", timeline="", product_interest="Analytics Dashboard")

add("e022", "support", 2, "ravi@lumenfold-studio.example.com",
    "How do I export reports to CSV?",
    """Hello, I can't find the export button for monthly reports. Where is it? Thanks, Ravi (Lumenfold Studio)""",
    company="Lumenfold Studio", contact_name="Ravi", email="ravi@lumenfold-studio.example.com",
    phone="", budget="", timeline="", product_interest="Analytics Dashboard")

add("e023", "support", 5, "it@tidewater-boats.example.com",
    "Production down - sync failing for all boats",
    """Our Field Service Scheduling sync has failed since last night and no bookings are visible. We have
customers on the dock right now. Please escalate. Ticket #48213. Contact: Dana Whitfield, 555-0102.
Tidewater Boat Rentals.""",
    company="Tidewater Boat Rentals", contact_name="Dana Whitfield", email="it@tidewater-boats.example.com",
    phone="555-0102", budget="", timeline="", product_interest="Field Service Scheduling")

add("e024", "support", 1, "k.lindqvist@pinecrest-books.example.com",
    "typo in welcome email",
    """Not a big deal but the welcome email says "Wecome to the team". Thought you'd want to know.
Karin Lindqvist, Pinecrest Books""",
    company="Pinecrest Books", contact_name="Karin Lindqvist", email="k.lindqvist@pinecrest-books.example.com",
    phone="", budget="", timeline="", product_interest="")

add("e025", "support", 3, "william.chu@oakhollow-clinic.example.com",
    "Password reset email never arrives",
    """I've requested a password reset 4 times and nothing arrives (checked spam). My username is wchu.
Oak Hollow Veterinary Clinic. Thanks - William Chu""",
    company="Oak Hollow Veterinary Clinic", contact_name="William Chu", email="william.chu@oakhollow-clinic.example.com",
    phone="", budget="", timeline="", product_interest="")

add("e026", "support", 3, "s.moreau@mosaic-retail.example.com",
    "Inventory counts differ between stores",
    """Hi, since Tuesday's update, Inventory Sync shows different counts for store 12 and store 14 for the
same SKU (RT-2291). Is this a known bug? Sylvie Moreau, Mosaic Retail Group.""",
    company="Mosaic Retail Group", contact_name="Sylvie Moreau", email="s.moreau@mosaic-retail.example.com",
    phone="", budget="", timeline="", product_interest="Inventory Sync")

add("e027", "support", 2, "ahmed.said@kestrel-law.example.com",
    "Add a new user to our account",
    """Please add Priscilla Grant (p.grant@kestrel-law.example.com) as a user on our Support Desk account.
Kind regards, Ahmed Said, Kestrel Legal LLP""",
    company="Kestrel Legal LLP", contact_name="Ahmed Said", email="ahmed.said@kestrel-law.example.com",
    phone="", budget="", timeline="", product_interest="Support Desk")

add("e028", "support", 4, "ops@vertexbuild.example.com",
    "Data missing after migration - urgent",
    """We imported our stock file yesterday and 1,200 SKUs are missing from Inventory Sync. We open warehouses
at 6am tomorrow and need them back. Hector Ruiz, Vertex Build Supply. 555-0166.""",
    company="Vertex Build Supply", contact_name="Hector Ruiz", email="ops@vertexbuild.example.com",
    phone="555-0166", budget="", timeline="before 6am tomorrow", product_interest="Inventory Sync")

add("e029", "support", 2, "grace.liu@brightpath-staffing.example.com",
    "Can't change the dashboard colour theme",
    """The theme setting reverts to light mode each time I log in. Minor, but annoying.
Grace Liu - Brightpath Staffing""",
    company="Brightpath Staffing", contact_name="Grace Liu", email="grace.liu@brightpath-staffing.example.com",
    phone="", budget="", timeline="", product_interest="Analytics Dashboard")

add("e030", "support", 3, "noah@sundial-bakery.example.com",
    "Mobile app crashes on login",
    """Since the last update the Android app closes right after I enter my password. Pixel 7, Android 15.
Noah from Sundial Bakery""",
    company="Sundial Bakery", contact_name="Noah", email="noah@sundial-bakery.example.com",
    phone="", budget="", timeline="", product_interest="mobile app")

# ---------------- invoice (8) ----------------
add("e031", "invoice", 3, "billing@paperplane-supplies.example.com",
    "Invoice #INV-20417 due 30 days",
    """Dear customer,

Please find attached invoice INV-20417 for $1,240.00 for office supplies delivered 3 November.
Payment is due within 30 days. Bank details are on the invoice.
Paperplane Supplies Accounts Team""",
    company="Paperplane Supplies", contact_name="", email="billing@paperplane-supplies.example.com",
    phone="", budget="$1,240.00", timeline="due within 30 days", product_interest="")

add("e032", "invoice", 4, "ar@cobaltcloud-hosting.example.com",
    "Overdue: invoice 88231",
    """Hello,

Our records show invoice 88231 ($3,860.50) from 2 October is now 14 days overdue. Please arrange payment
this week to avoid service suspension. Questions: accounts receivable, 555-0170. - Marcus Bell, Cobalt Cloud Hosting""",
    company="Cobalt Cloud Hosting", contact_name="Marcus Bell", email="ar@cobaltcloud-hosting.example.com",
    phone="555-0170", budget="$3,860.50", timeline="payment this week", product_interest="")

add("e033", "invoice", 2, "no-reply@stellar-telecom.example.com",
    "Your November statement is ready",
    """Your Stellar Telecom statement for November is ready. Amount due: $212.18. Due date: 12 December.
Log in to your account to view and pay.""",
    company="Stellar Telecom", contact_name="", email="no-reply@stellar-telecom.example.com",
    phone="", budget="$212.18", timeline="due 12 December", product_interest="")

add("e034", "invoice", 3, "finance@lakeshore-legal.example.com",
    "Receipt for retainer payment",
    """Hi, thank you for your payment of $5,000 on 18 November. Attached is your receipt for the retainer
(ref RET-7730). No further action is needed. Priya Shah, Lakeshore Legal Finance""",
    company="Lakeshore Legal", contact_name="Priya Shah", email="finance@lakeshore-legal.example.com",
    phone="", budget="$5,000", timeline="", product_interest="")

add("e035", "invoice", 4, "j.moreno@orchard-print.example.com",
    "Please send us your W-9 and updated bank details",
    """Hi, Julia Moreno from Orchard Print accounts payable. To process your invoice INV-0092 for $2,400
we need your W-9 and bank details by Friday, otherwise payment moves to the next cycle.""",
    company="Orchard Print", contact_name="Julia Moreno", email="j.moreno@orchard-print.example.com",
    phone="", budget="$2,400", timeline="by Friday", product_interest="")

add("e036", "invoice", 2, "subscriptions@datawell.example.com",
    "Subscription renewal invoice",
    """Your annual DataWell plan renews on 3 January. An invoice for $948.00 has been generated. You don't
need to do anything if your card on file is current. DataWell Billing""",
    company="DataWell", contact_name="", email="subscriptions@datawell.example.com",
    phone="", budget="$948.00", timeline="renews 3 January", product_interest="")

add("e037", "invoice", 3, "elena.rossi@meridian-courier.example.com",
    "Credit note CN-311",
    """Hi, we've issued credit note CN-311 for $180 against last month's delivery overcharge. It will be applied to
your next invoice. Regards, Elena Rossi, Meridian Courier Services""",
    company="Meridian Courier Services", contact_name="Elena Rossi", email="elena.rossi@meridian-courier.example.com",
    phone="", budget="$180", timeline="", product_interest="")

add("e038", "invoice", 5, "collections@ironbridge-equipment.example.com",
    "FINAL NOTICE - payment required in 48 hours",
    """Final notice: invoice 5521 ($14,750) is 60 days overdue. Unless payment is received within 48 hours we
will refer the account to collections. Contact David Chen on 555-0121. Ironbridge Equipment Rental""",
    company="Ironbridge Equipment Rental", contact_name="David Chen", email="collections@ironbridge-equipment.example.com",
    phone="555-0121", budget="$14,750", timeline="within 48 hours", product_interest="")

# ---------------- spam (7) ----------------
add("e039", "spam", 1, "promo@seo-boost-now.example.com",
    "Rank #1 on Google in 7 days GUARANTEED",
    """Dear Sir/Madam, our SEO experts will put your website on page one of Google within 7 days or your money
back. Only $99! Reply now to claim this limited offer. Unsubscribe at the bottom.""",
    company="", contact_name="", email="promo@seo-boost-now.example.com",
    phone="", budget="$99", timeline="7 days", product_interest="SEO services")

add("e040", "spam", 1, "winner@lucky-draw-intl.example.com",
    "Congratulations!! You won $1,000,000",
    """You have been selected as the winner of our international lottery. To claim your $1,000,000 prize send
your full name, address and bank account number. Act within 24 hours!""",
    company="", contact_name="", email="winner@lucky-draw-intl.example.com",
    phone="", budget="$1,000,000", timeline="within 24 hours", product_interest="")

add("e041", "spam", 2, "security@acc0unt-verify.example.com",
    "Your account will be suspended - verify now",
    """Dear user, we detected unusual activity. Click the link below and enter your password within 12 hours
or your account will be permanently closed. http://verify-account.example.com/login""",
    company="", contact_name="", email="security@acc0unt-verify.example.com",
    phone="", budget="", timeline="within 12 hours", product_interest="")

add("e042", "spam", 1, "kate@growthhacks-outreach.example.com",
    "Quick question about your website",
    """Hi there, I'm Kate and I help businesses like yours get 10x more leads with cold email automation.
Can I send you a free audit? We have worked with 500+ clients. Let me know! P.S. We also sell email lists.""",
    company="GrowthHacks Outreach", contact_name="Kate", email="kate@growthhacks-outreach.example.com",
    phone="", budget="", timeline="", product_interest="cold email automation")

add("e043", "spam", 1, "deals@cheapmeds-online.example.com",
    "Cheap meds no prescription",
    """Buy all your medications at 90% off, no prescription needed. Worldwide delivery. Order today at
cheapmeds-online.example.com""",
    company="", contact_name="", email="deals@cheapmeds-online.example.com",
    phone="", budget="", timeline="", product_interest="")

add("e044", "spam", 1, "invest@cryptomax-signals.example.com",
    "Double your Bitcoin in 48 hours",
    """Join our private signals group and turn $500 into $5,000 in 48 hours. Guaranteed returns, limited
spots. Reply YES for the link.""",
    company="", contact_name="", email="invest@cryptomax-signals.example.com",
    phone="", budget="$500", timeline="48 hours", product_interest="")

add("e045", "spam", 1, "outreach@leadlist-pro.example.com",
    "Buy verified B2B leads - 100k contacts $149",
    """Hello, we sell verified B2B email lists, 100,000 contacts for only $149. Industry-specific, instantly
downloadable. Reply to get a sample.""",
    company="", contact_name="", email="outreach@leadlist-pro.example.com",
    phone="", budget="$149", timeline="", product_interest="B2B email lists")

# ---------------- other (6) ----------------
add("e046", "other", 2, "recruiter@talentbridge.example.com",
    "Opportunity for your senior engineer",
    """Hi, I'm Olivia Grant, a recruiter at TalentBridge. I'd love to talk to someone on your engineering team
about a role at one of our clients. Could you forward this to the right person?""",
    company="TalentBridge", contact_name="Olivia Grant", email="recruiter@talentbridge.example.com",
    phone="", budget="", timeline="", product_interest="")

add("e047", "other", 2, "events@citybiz-forum.example.com",
    "Invitation: Regional Business Forum, 14 March",
    """You're invited to speak or attend the Regional Business Forum on 14 March. Early-bird registration
closes 1 February. Contact Paul Sterling, events manager, at events@citybiz-forum.example.com.""",
    company="CityBiz Forum", contact_name="Paul Sterling", email="events@citybiz-forum.example.com",
    phone="", budget="", timeline="14 March", product_interest="")

add("e048", "other", 1, "mia.berg@example.com",
    "Thanks!",
    """Just wanted to say thanks for the quick help last week. Great service. - Mia Berg""",
    company="", contact_name="Mia Berg", email="mia.berg@example.com",
    phone="", budget="", timeline="", product_interest="")

add("e049", "other", 2, "press@techdigest-weekly.example.com",
    "Interview request for our newsletter",
    """Hi, I'm Raj Patel from Tech Digest Weekly. We're writing about workflow automation in small
businesses and would like a 15-minute interview with someone from your team in the next two weeks.""",
    company="Tech Digest Weekly", contact_name="Raj Patel", email="press@techdigest-weekly.example.com",
    phone="", budget="", timeline="within the next two weeks", product_interest="")

add("e050", "other", 3, "legal@harbor-and-finch.example.com",
    "Data processing agreement for your review",
    """Hello, attached is the standard data processing addendum for our vendor onboarding. Please have your
legal team review and return a signed copy by 20 December. Camille Finch, Harbor & Finch LLP""",
    company="Harbor & Finch LLP", contact_name="Camille Finch", email="legal@harbor-and-finch.example.com",
    phone="", budget="", timeline="by 20 December", product_interest="")

add("e051", "other", 1, "unknown.sender@example.com",
    "Re: Re: Fwd:",
    """see below

> ok""",
    company="", contact_name="", email="unknown.sender@example.com",
    phone="", budget="", timeline="", product_interest="")

# deliberately malformed inputs that must hit the error branch
INVALID = [
    {"id": "bad1", "from": "not-an-email", "subject": "Hello", "body": "Please call me about pricing."},
    {"id": "bad2", "from": "empty.body@example.com", "subject": "(no body)", "body": "   "},
    {"id": "bad3", "from": "", "subject": "missing sender", "body": "We would like a quote for Support Desk."},
    {"id": "bad4", "subject": "no from field at all"},
]


def main():
    (ROOT / "sample_data").mkdir(exist_ok=True)
    with open(ROOT / "sample_data/emails.jsonl", "w") as f:
        for e in E:
            f.write(json.dumps({k: e[k] for k in ("id", "from", "subject", "body")}, ensure_ascii=False) + "\n")
    with open(ROOT / "sample_data/invalid_emails.jsonl", "w") as f:
        for e in INVALID:
            f.write(json.dumps(e) + "\n")
    with open(ROOT / "eval/labels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "intent", *FIELDS, "urgency"])
        for e in E:
            w.writerow([e["id"], e["intent"], *[e["labels"].get(k, "") for k in FIELDS], e["urgency"]])
    print(len(E), "emails,", len(INVALID), "invalid")


if __name__ == "__main__":
    main()
