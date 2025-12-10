#!/usr/bin/env python3
"""
Send Team Content Strategy Email V2 - with Bani's specific guidance
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
h4 {
    color: #1a1a1a;
    font-size: 16px;
    margin-top: 20px;
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
.key-box {
    background: #fffbeb;
    border: 2px solid #c9a227;
    padding: 20px;
    margin: 20px 0;
    border-radius: 4px;
}
.key-box h4 {
    margin-top: 0;
    color: #92400e;
}
.balance-box {
    background: #f9f9f9;
    border: 2px solid #c9a227;
    padding: 25px;
    margin: 30px 0;
    border-radius: 4px;
}
.balance-grid {
    display: table;
    width: 100%;
}
.balance-item {
    display: table-cell;
    width: 33%;
    text-align: center;
    padding: 15px;
    vertical-align: top;
}
.balance-item h4 {
    color: #c9a227;
    margin: 0 0 10px 0;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.balance-item p {
    margin: 0;
    font-size: 14px;
    color: #666;
}
.balance-item .quote {
    font-style: italic;
    margin-top: 10px;
    color: #999;
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
.checklist {
    background: #f9f9f9;
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
}
.checklist h4 {
    margin-top: 0;
    color: #c9a227;
}
.checklist ul {
    list-style: none;
    padding: 0;
    margin: 0;
}
.checklist li {
    margin: 8px 0;
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
    font-weight: bold;
}
.voice-bad .voice-label { color: #dc2626; }
.voice-good .voice-label { color: #16a34a; }
.format-box {
    background: #1a1a1a;
    color: #f0f0f0;
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
    font-family: monospace;
    font-size: 13px;
    line-height: 1.6;
}
.format-box .label {
    color: #c9a227;
    font-weight: bold;
}
.tone-box {
    background: #fef2f2;
    border: 2px solid #dc2626;
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
}
.tone-box h4 {
    margin-top: 0;
    color: #dc2626;
}
.tone-box ul {
    margin: 0;
    padding-left: 20px;
}
.tone-box li {
    margin: 8px 0;
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
.workflow-box {
    background: #f9f9f9;
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
    font-family: monospace;
    font-size: 13px;
}
.workflow-box .day {
    color: #c9a227;
    font-weight: bold;
}
.two-column {
    display: table;
    width: 100%;
    margin: 20px 0;
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
}
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
ul.do-list, ul.dont-list {
    padding-left: 20px;
}
ul.do-list li { color: #166534; margin: 8px 0; }
ul.dont-list li { color: #dc2626; margin: 8px 0; }
.timeline-box {
    background: #f0fdf4;
    border: 2px solid #22c55e;
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
}
.timeline-box h4 {
    margin-top: 0;
    color: #166534;
}
</style>
</head>
<body>
<div class="container">

<h1>BENSLEY CONTENT STRATEGY</h1>
<p style="color: #666; margin-top: -20px;">For the Creative Team</p>

<div class="highlight-box">
<p><strong>The Big Idea:</strong> We're shifting from "showcasing Bensley" to "teaching Bensley"</p>
</div>

<p>Every piece of content should answer: <em>"What will someone learn from this that they'll remember in 5 years?"</em></p>

<h2>THE TWO TRACKS</h2>

<p>We're splitting into two distinct but intimately connected tracks:</p>

<div class="two-column">
<div class="column">
<h4>Track 1: Aubrey &mdash; Personal Bill</h4>
<p><strong>Theme:</strong> "Who Bill is"</p>
<p><strong>Format:</strong> Carousels</p>
<p>Bill the person &mdash; his favorites, his art, his direct voice and philosophy</p>
<ul>
<li>Favorite Books series</li>
<li>Favorite Designers series</li>
<li>Favorite Artists (Bill's painting journey)</li>
<li>Philosophy quotes</li>
</ul>
</div>
<div class="column">
<h4>Track 2: Bani &mdash; Bensley as Business</h4>
<p><strong>Theme:</strong> "Who Bensley is"</p>
<p><strong>Format:</strong> Reels</p>
<p>The studio &mdash; why Bensley isn't just Bill. The team embodies the philosophy.</p>
<ul>
<li>Project Postcards (The Siam, Khao Yai, etc.)</li>
<li>Team Spotlights (P'Mum, Brian, designers)</li>
<li>Process Stories (Antique lifecycle)</li>
</ul>
</div>
</div>

<div class="key-box">
<h4>The Key Idea for Bani's Track</h4>
<p><strong>Bensley is a collection of people who embody and instill the blueprint and philosophy of Bill Bensley.</strong></p>
<p>The enthusiasm, creativity, environmental stewardship, and sense of community runs through everyone &mdash; not just Bill. Show that.</p>
</div>

<h2>TONE FOR BANI'S CONTENT</h2>

<div class="tone-box">
<h4>Important: The Tone Shift</h4>
<ul>
<li><strong>Less kiddy</strong> &mdash; more professional and mature</li>
<li><strong>Thoughtful but creative</strong> &mdash; not just pretty shots</li>
<li><strong>Show substance</strong> &mdash; the WHY behind what we do</li>
<li><strong>Team as embodiment</strong> &mdash; everyone carries the philosophy</li>
</ul>
</div>

<p>P'Mum's video is a great example &mdash; it shows the enthusiasm of team members, how ideas and creativity are fostered throughout the studio, and the environmental stewardship and sense of community that all the designers embody.</p>

<h2>THE CONTENT BALANCE</h2>

<p>Every post needs to hit <strong>three elements</strong>:</p>

<div class="balance-box">
<div class="balance-grid">
<div class="balance-item">
<h4>Visually Stunning</h4>
<p>Eye-catching hook that stops the scroll</p>
<p class="quote">"Wow, what is this?"</p>
</div>
<div class="balance-item">
<h4>Storytelling</h4>
<p>Narrative flow that keeps them watching</p>
<p class="quote">"Tell me more..."</p>
</div>
<div class="balance-item">
<h4>Insight</h4>
<p>Real value they take away</p>
<p class="quote">"I learned something"</p>
</div>
</div>
</div>

<p><strong>If a post is missing any of these three, it's not ready.</strong></p>

<h2>CONTENT THEMES FOR BANI</h2>

<h3>1. Project Postcards</h3>
<p>Deep-dive into Bensley properties. Every project gets the same treatment:</p>

<div class="format-box">
<span class="label">1. THE CHALLENGE</span><br>
"We were given a narrow site near a busy road..."<br>
What we started with, what the constraints were<br><br>

<span class="label">2. THE NARRATIVE</span><br>
"We created the story of Som Sak, the train conductor..."<br>
The imaginative leap, the creative solution<br><br>

<span class="label">3. THE JOURNEY</span><br>
Walk through the space, show the magic moments<br>
Let viewers experience it<br><br>

<span class="label">4. THE PHILOSOPHY</span><br>
End with the lesson, the insight<br>
"The constraint became the magic"
</div>

<p><strong>Upcoming properties:</strong> The Siam, InterCon Khao Yai (Jan 13), Four Seasons Koh Samui, Chiang Mai, Chiang Rai</p>

<h3>2. Team Spotlights</h3>
<p>Individual designers and staff showing their enthusiasm, ideas, and creativity. How they embody the Bensley philosophy.</p>
<p><strong>Examples:</strong> P'Mum & the boat, Brian's Siam walkthrough</p>

<h3>3. Antique Lifecycle (NEW)</h3>
<p>Follow items through their journey:</p>
<p style="text-align: center; font-size: 16px;"><strong>Warehouse &rarr; Bill's house &rarr; Office &rarr; Refurbishment &rarr; Hotel</strong></p>

<div class="key-box">
<h4>Critical: Add the WHY Layer</h4>
<p>The visual journey is cool, but <strong>don't just make a cool video</strong>. Combine:</p>
<ul>
<li><strong>Visual:</strong> The journey of the antique</li>
<li><strong>Narrative:</strong> The story of this specific piece</li>
<li><strong>Philosophy:</strong> Why do we recycle and repurpose? What's the meaning?</li>
</ul>
<p>Sustainability + storytelling + craft = substance</p>
</div>

<h2>THE THREE PILLARS</h2>

<p>Every post should map to one of these:</p>

<div class="pillar">
<h4>1. Truth to Place</h4>
<blockquote>"With hotels, we have the wonderful opportunity to create an alternate universe for people."</blockquote>
<p>Every decision anchored in culture, climate, landscape, craft, and history.</p>
</div>

<div class="pillar">
<h4>2. Sustainability & Stewardship</h4>
<blockquote>"High Yield, Low Impact. We want projects that give back more than they take."</blockquote>
<p>No greenwashing. Real impact. "Minimal Intervention."</p>
</div>

<div class="pillar">
<h4>3. Joyful Originality</h4>
<blockquote>"Lebih gila, lebih baik &mdash; The crazier, the better."</blockquote>
<p>Bold, witty, exuberant &mdash; and rigorously considered.</p>
</div>

<h2>THE BENSLEY VOICE</h2>

<div class="voice-comparison">
<div class="voice-box voice-bad">
<div class="voice-label">&#10060; Generic luxury</div>
<p>"The resort features 50 luxuriously appointed villas with stunning ocean views and world-class amenities."</p>
</div>
<div class="voice-box voice-good">
<div class="voice-label">&#10004; Bensley</div>
<p>"We kept all 856 coconut trees at Four Seasons Koh Samui. The villas weave between them like they've always been there. You wake up to monkeys, not marble lobbies."</p>
</div>
</div>

<p><strong>The difference:</strong> Specific details. A story. A point of view. Something memorable.</p>

<h2>IMMEDIATE TIMELINE</h2>

<div class="timeline-box">
<h4>This Week (Before Christmas)</h4>
<ul>
<li><strong>The Siam content</strong> &mdash; Brian's walkthrough shots (aim to post tomorrow)</li>
<li><strong>P'Mum & the boat</strong> &mdash; finalize and post</li>
<li><strong>Aubrey starts posting</strong> &mdash; first carousels go live next week</li>
</ul>

<h4>Christmas Break</h4>
<ul>
<li><strong>Gatsby party shoot</strong> &mdash; New Year's Eve area (can be fun/quirky &mdash; comes after educational content is out)</li>
<li><strong>Sign off the year</strong> &mdash; team celebration content</li>
</ul>

<h4>January</h4>
<ul>
<li><strong>Khao Yai shoot</strong> &mdash; January 13th (Som Sak narrative)</li>
<li><strong>Continue project Postcards</strong></li>
</ul>

<h4>Q1 2025</h4>
<ul>
<li>Four Seasons Koh Samui</li>
<li>Four Seasons Chiang Mai</li>
<li>Four Seasons Chiang Rai</li>
<li>Antique Lifecycle series</li>
</ul>
</div>

<h2>POSTING SCHEDULE</h2>

<p><strong>Target: 3-4 posts per week</strong></p>

<table>
<tr><th>Day</th><th>Content Type</th><th>Track</th></tr>
<tr><td>Monday</td><td>Philosophy quote</td><td>Aubrey</td></tr>
<tr><td>Wednesday</td><td>Educational carousel</td><td>Aubrey</td></tr>
<tr><td>Friday</td><td>Reel (Postcard or Team Spotlight)</td><td>Bani</td></tr>
<tr><td>Sunday</td><td>Behind-the-scenes / teaser</td><td>Either</td></tr>
</table>

<h2>THE CONTENT TEST</h2>

<p>Before publishing, check:</p>

<div class="checklist">
<ul>
<li><strong>Visual:</strong> Does this stop the scroll?</li>
<li><strong>Story:</strong> Is there a narrative arc? A WHY, not just WHAT?</li>
<li><strong>Insight:</strong> What's the one thing someone will remember?</li>
<li><strong>Pillar:</strong> Does it fit Truth to Place, Sustainability, or Joyful Originality?</li>
<li><strong>Voice:</strong> Does it sound like Bensley, not generic luxury?</li>
</ul>
</div>

<div class="test-box">
<p>"Will someone remember this in 5 years?<br>Will it change how they think about design?"</p>
<p class="subtext">If yes &rarr; publish | If no &rarr; rework</p>
</div>

<h2>SUMMARY</h2>

<table class="summary-table">
<tr><th>Track</th><th>Person</th><th>Format</th><th>Focus</th></tr>
<tr><td>Personal Bill</td><td>Aubrey</td><td>Carousels</td><td>Bill the person &mdash; favorites, art, his voice</td></tr>
<tr><td>Bensley as Business</td><td>Bani</td><td>Reels</td><td>The studio &mdash; team, process, philosophy embodied</td></tr>
</table>

<p style="margin-top: 30px; text-align: center;">
<strong>The distinction:</strong><br>
Aubrey = "Who Bill is" (personal, direct from Bill)<br>
Bani = "Who Bensley is" (the team, why it's not just Bill)<br><br>
<strong>The tone:</strong> Less kiddy, more professional/mature, thoughtful but creative<br>
<strong>The balance:</strong> Visual + Story + Insight<br>
<strong>The test:</strong> Will they remember this in 5 years?
</p>

<div class="footer">
<p>Questions? Let's discuss.</p>
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
msg['Subject'] = "BENSLEY Content Strategy - Team Guide (Updated)"

# Attach HTML
msg.attach(MIMEText(html_content, 'html'))

# Send
print(f"Sending Updated Content Strategy to {smtp_user}...")

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
