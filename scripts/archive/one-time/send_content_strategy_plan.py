#!/usr/bin/env python3
"""
Send Content Strategy Plan Email - HTML formatted
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Email configuration
smtp_host = "tmail.bensley.com"
smtp_port = 587
smtp_user = "lukas@bensley.com"
smtp_password = "0823356345"

html_content = """
<!DOCTYPE html>
<html>
<head>
<style>
body {
    font-family: 'Georgia', serif;
    line-height: 1.7;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #fafafa;
}
.container {
    background: white;
    padding: 40px;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
h1 {
    color: #1a1a1a;
    font-size: 28px;
    border-bottom: 3px solid #c9a227;
    padding-bottom: 15px;
    margin-bottom: 30px;
}
h2 {
    color: #1a1a1a;
    font-size: 22px;
    margin-top: 40px;
    border-left: 4px solid #c9a227;
    padding-left: 15px;
}
h3 {
    color: #444;
    font-size: 18px;
    margin-top: 25px;
}
.highlight-box {
    background: #1a1a1a;
    color: white;
    padding: 25px;
    margin: 30px 0;
    border-radius: 4px;
    text-align: center;
}
.highlight-box p {
    font-size: 18px;
    margin: 0;
}
.highlight-box .shift {
    font-size: 14px;
    color: #c9a227;
    margin-top: 10px;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 14px;
}
th {
    background: #1a1a1a;
    color: white;
    padding: 12px 15px;
    text-align: left;
}
td {
    padding: 12px 15px;
    border-bottom: 1px solid #eee;
}
tr:hover {
    background: #f9f9f9;
}
.pillar {
    background: #f9f9f9;
    padding: 20px;
    margin: 15px 0;
    border-radius: 4px;
    border-left: 4px solid #c9a227;
}
.pillar h4 {
    margin-top: 0;
    color: #1a1a1a;
}
blockquote {
    border-left: 4px solid #c9a227;
    margin: 20px 0;
    padding: 15px 20px;
    background: #fafafa;
    font-style: italic;
    color: #555;
}
.two-column {
    display: table;
    width: 100%;
    margin: 30px 0;
}
.column {
    display: table-cell;
    width: 48%;
    padding: 20px;
    vertical-align: top;
    background: #f9f9f9;
    border-radius: 4px;
}
.column:first-child {
    margin-right: 4%;
    border-right: 2px solid #c9a227;
}
.column h4 {
    color: #c9a227;
    margin-top: 0;
    font-size: 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.metrics-box {
    background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
    color: white;
    padding: 30px;
    border-radius: 4px;
    margin: 30px 0;
}
.metrics-box h3 {
    color: #c9a227;
    margin-top: 0;
}
.metric {
    display: inline-block;
    text-align: center;
    width: 30%;
    padding: 15px;
}
.metric .number {
    font-size: 36px;
    font-weight: bold;
    color: #c9a227;
}
.metric .label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #999;
}
.checklist {
    background: #f9f9f9;
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
}
.checklist li {
    margin: 10px 0;
    list-style: none;
    padding-left: 25px;
    position: relative;
}
.checklist li:before {
    content: "[ ]";
    position: absolute;
    left: 0;
    color: #c9a227;
    font-family: monospace;
}
.test-box {
    background: #1a1a1a;
    color: white;
    padding: 30px;
    text-align: center;
    margin: 40px 0;
    border-radius: 4px;
}
.test-box p {
    font-size: 20px;
    font-style: italic;
    margin: 0;
}
.test-box .subtext {
    font-size: 14px;
    margin-top: 15px;
    font-style: normal;
    color: #999;
}
.voice-comparison {
    display: table;
    width: 100%;
    margin: 20px 0;
}
.voice-box {
    display: table-cell;
    width: 48%;
    padding: 20px;
    vertical-align: top;
}
.voice-bad {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 4px;
}
.voice-good {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 4px;
}
.voice-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
}
.voice-bad .voice-label { color: #dc2626; }
.voice-good .voice-label { color: #16a34a; }
.summary-table {
    background: #1a1a1a;
    color: white;
    border-radius: 4px;
    overflow: hidden;
}
.summary-table th {
    background: #c9a227;
    color: #1a1a1a;
}
.summary-table td {
    border-bottom: 1px solid #333;
}
.footer {
    margin-top: 50px;
    padding-top: 20px;
    border-top: 1px solid #eee;
    color: #666;
    font-size: 14px;
}
.gold { color: #c9a227; }
.calendar-week {
    margin: 20px 0;
    padding: 15px;
    background: #f9f9f9;
    border-radius: 4px;
}
.calendar-week h4 {
    margin-top: 0;
    color: #1a1a1a;
}
</style>
</head>
<body>
<div class="container">

<h1>BENSLEY CONTENT STRATEGY PLAN</h1>

<div class="highlight-box">
<p><strong>The Shift:</strong> From showcasing Bensley to teaching Bensley</p>
<p class="shift">From: Whimsical, niche &rarr; To: Professional storytelling, broader appeal</p>
</div>

<p><strong>Test for every post:</strong> <em>"What will someone learn from this that they'll remember in 5 years?"</em></p>

<h2>GOALS & METRICS</h2>

<div class="metrics-box">
<div class="metric">
<div class="number">65K</div>
<div class="label">Current Followers</div>
</div>
<div class="metric">
<div class="number">100K</div>
<div class="label">6-Month Target</div>
</div>
<div class="metric">
<div class="number">7-10%</div>
<div class="label">Monthly Growth</div>
</div>
</div>

<p><strong>Business Goals:</strong></p>
<ul>
<li>Brand awareness (Bensley Design Studios as entity, not just "Bill's company")</li>
<li>Portfolio showcase for potential clients</li>
<li>Lead generation for projects</li>
<li>ESCAPISM 3 content pipeline</li>
<li>Reach beyond niche &rarr; design enthusiasts, hospitality industry, general public</li>
</ul>

<h2>TEAM STRUCTURE</h2>

<div class="two-column">
<div class="column">
<h4>Track 1: Aubrey (In-House)</h4>
<p><strong>Educational Series</strong></p>
<ul>
<li>Carousels (8/month)</li>
<li>Quote graphics</li>
<li>Templates/formats</li>
<li>Support: Fah + AI tools</li>
</ul>
<p><em>"What Bill knows"</em></p>
</div>
<div class="column">
<h4>Track 2: Bani (Field)</h4>
<p><strong>40K baht/month</strong></p>
<ul>
<li>Reels (4/month)</li>
<li>Postcard Series</li>
<li>Quick Hits</li>
<li>On-location shoots</li>
</ul>
<p><em>"What Bensley creates"</em></p>
<p style="color: #dc2626;"><strong>5-day max turnaround rule</strong></p>
</div>
</div>

<h2>CONTENT PILLARS</h2>

<div class="pillar">
<h4>1. Truth to Place</h4>
<p><em>"We don't design hotels. We design stories anchored in place."</em></p>
<p>Site research, local culture, history. Why decisions were made (not just what looks good).</p>
</div>

<div class="pillar">
<h4>2. Sustainability & Stewardship</h4>
<p><em>"High Yield, Low Impact"</em></p>
<p>Minimal intervention (building around trees, not cutting them). Real impact metrics. Conservation stories.</p>
</div>

<div class="pillar">
<h4>3. Joyful Originality</h4>
<p><em>"Lebih gila, lebih baik &mdash; The crazier, the better"</em></p>
<p>Bold choices that worked. Constraint &rarr; Magic stories. The Bensley vibe.</p>
</div>

<h2>CONTENT FORMATS</h2>

<h3>Aubrey: Educational Carousels</h3>

<table>
<tr><th>Series</th><th>Content Source</th><th>Frequency</th></tr>
<tr><td>Favorite Books</td><td>Bill's commentary (provided)</td><td>2x/month</td></tr>
<tr><td>Favorite Designers</td><td>Bill's origin story + list</td><td>2x/month</td></tr>
<tr><td>Favorite Hotels</td><td>Need from Bill</td><td>Future</td></tr>
<tr><td>Design Philosophy</td><td>Extract from interviews</td><td>Future</td></tr>
</table>

<p><strong>Key Change:</strong> NO MORE cramming 10 things into one video. 1-2 items per post. Go deeper. Build series over weeks.</p>

<h3>Bani: Narrative Storytelling</h3>

<p><strong>Postcard Series (Deep-Dive Projects):</strong></p>
<ol>
<li><strong>The Challenge</strong> &mdash; Site, constraints</li>
<li><strong>The Narrative</strong> &mdash; Story we created</li>
<li><strong>The Journey</strong> &mdash; Walk through magic moments</li>
<li><strong>The Philosophy</strong> &mdash; End with lesson</li>
</ol>

<table>
<tr><th>Project</th><th>Story</th><th>Status</th></tr>
<tr><td>The Siam</td><td>Museum hotel, antique journey</td><td>Ready to shoot</td></tr>
<tr><td>InterCon Khao Yai</td><td>Som Sak the train conductor</td><td>Jan shoot (confirm)</td></tr>
<tr><td>Four Seasons Koh Samui</td><td>856 coconut trees</td><td>Check footage</td></tr>
<tr><td>Capella Ubud</td><td>Zero trees cut</td><td>Check footage</td></tr>
<tr><td>Shinta Mani Wild</td><td>Zipline + rangers</td><td>Check footage</td></tr>
</table>

<h2>MONTHLY CALENDAR</h2>

<p><strong>Target: 12-16 posts/month (3-4x per week)</strong></p>

<div class="calendar-week">
<h4>Weekly Rhythm</h4>
<table>
<tr><th>Day</th><th>Content</th><th>Owner</th></tr>
<tr><td>Monday</td><td>Philosophy quote</td><td>Aubrey</td></tr>
<tr><td>Wednesday</td><td>Carousel (educational series)</td><td>Aubrey</td></tr>
<tr><td>Friday</td><td>Reel (Postcard or Quick Hit)</td><td>Bani</td></tr>
<tr><td>Sunday</td><td>Behind-the-scenes or teaser</td><td>Either</td></tr>
</table>
</div>

<p><strong>Monthly Totals:</strong> 4 quotes + 4 carousels + 4 reels + 4 BTS = 16 posts</p>

<h2>THE BENSLEY VOICE</h2>

<div class="voice-comparison">
<div class="voice-box voice-bad">
<div class="voice-label">Not This</div>
<p>"The resort features 50 luxuriously appointed villas with stunning ocean views and world-class amenities."</p>
</div>
<div class="voice-box voice-good">
<div class="voice-label">This</div>
<p>"We kept all 856 coconut trees. The villas weave between them like they've always been there. You wake up to monkeys, not marble lobbies."</p>
</div>
</div>

<h2>VOICE CLONE OPTION</h2>

<p>Test AI voice cloning for Bill's voiceovers &mdash; could speed up production significantly.</p>
<p><strong>Action:</strong> Ask Bill if he's open to testing. If yes, clone from existing audio, test on 1 carousel, get feedback.</p>

<h2>IMMEDIATE NEXT STEPS</h2>

<h3>This Week (December)</h3>
<ul class="checklist">
<li><strong>Gatsby shoot (Friday)</strong> &mdash; Bani captures, elegant not whacky</li>
<li><strong>Audit existing footage</strong> &mdash; What do we have for each project?</li>
<li><strong>Create carousel template</strong> &mdash; Aubrey designs reusable format</li>
<li><strong>Ask Bill about voice clone</strong> &mdash; Get yes/no</li>
<li><strong>Brief Aubrey on Books #1-2</strong> &mdash; First carousel in new format</li>
</ul>

<h3>January</h3>
<ul class="checklist">
<li>Confirm InterCon Khao Yai shoot (Som Sak Postcard)</li>
<li>Launch Favorite Books series (2 posts)</li>
<li>Launch Favorite Designers series (origin story + 2 designers)</li>
<li>Complete P'Mum + Brian Reels</li>
<li>Set up content tracking spreadsheet</li>
</ul>

<h3>Q1 2025</h3>
<ul class="checklist">
<li>Establish 3-4x/week posting rhythm</li>
<li>Build Postcard backlog (3 projects shot)</li>
<li>Develop Design Philosophy series</li>
<li>Hit 80K followers milestone</li>
</ul>

<h2>BUDGET ALLOCATION</h2>

<table>
<tr><th>Item</th><th>Cost</th><th>Quantity</th></tr>
<tr><td>Postcard Reel</td><td>15,000 baht</td><td>2/month</td></tr>
<tr><td>Quick Hit Reel</td><td>5,000 baht</td><td>2/month</td></tr>
<tr><td><strong>Bani Total</strong></td><td><strong>40,000 baht</strong></td><td>4 reels</td></tr>
<tr><td>Aubrey</td><td>Salaried</td><td>8 carousels</td></tr>
</table>

<div class="test-box">
<p>"Will someone remember this in 5 years?<br>Will it change how they think about design?"</p>
<p class="subtext">If yes &mdash; publish. If no &mdash; rethink.</p>
</div>

<h2>SUMMARY</h2>

<table class="summary-table">
<tr><th>Track</th><th>Owner</th><th>Format</th><th>Output</th></tr>
<tr><td>Educational</td><td>Aubrey</td><td>Carousels</td><td>8/month</td></tr>
<tr><td>Narrative</td><td>Bani</td><td>Reels</td><td>4/month</td></tr>
<tr><td>Direction</td><td>Lukas</td><td>&mdash;</td><td>&mdash;</td></tr>
<tr><td>Approval</td><td>Bill</td><td>&mdash;</td><td>&mdash;</td></tr>
</table>

<p style="margin-top: 30px;"><strong>The goal:</strong> When someone follows Bensley, they learn something. When they think of design, they think of your philosophy. When they see a Bensley property, they understand WHY it feels different.</p>

<p><strong>Everything feeds into the bigger picture:</strong> Instagram today, ESCAPISM 3 tomorrow, the Bensley Bible forever.</p>

<div class="footer">
<p>Questions or changes needed? Reply to this email.</p>
<p>&mdash; Lukas</p>
</div>

</div>
</body>
</html>
"""

# Create email
msg = MIMEMultipart('alternative')
msg['From'] = smtp_user
msg['To'] = smtp_user
msg['Subject'] = "BENSLEY Content Strategy Plan - December 2025"

# Attach HTML
msg.attach(MIMEText(html_content, 'html'))

# Send
print(f"Sending Content Strategy Plan to {smtp_user}...")

try:
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print(f"TLS failed: {e}")
    print("Trying SSL on port 465...")
    try:
        with smtplib.SMTP_SSL(smtp_host, 465, timeout=30) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print("Email sent successfully via SSL!")
    except Exception as e2:
        print(f"SSL also failed: {e2}")
