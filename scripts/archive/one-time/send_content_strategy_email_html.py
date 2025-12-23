#!/usr/bin/env python3
"""
Send Content Strategy Email - HTML formatted
"""

import smtplib
import os
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
    line-height: 1.6;
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
    margin-top: 30px;
}
.header-meta {
    color: #666;
    font-size: 14px;
    margin-bottom: 30px;
    padding: 15px;
    background: #f5f5f5;
    border-radius: 4px;
}
.intro {
    font-size: 18px;
    color: #444;
    margin-bottom: 30px;
}
.highlight {
    background: linear-gradient(to bottom, transparent 60%, #fff3cd 60%);
    font-weight: bold;
}
blockquote {
    border-left: 4px solid #c9a227;
    margin: 20px 0;
    padding: 15px 20px;
    background: #fafafa;
    font-style: italic;
    color: #555;
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
.deliverable {
    padding: 8px 0;
    border-bottom: 1px dashed #ddd;
}
.deliverable:last-child {
    border-bottom: none;
}
.status-progress {
    color: #d97706;
    font-weight: bold;
}
.status-friday {
    color: #dc2626;
    font-weight: bold;
}
.book-entry {
    margin: 15px 0;
    padding: 15px;
    background: #fafafa;
    border-radius: 4px;
}
.book-title {
    font-weight: bold;
    color: #1a1a1a;
}
.book-author {
    color: #666;
    font-size: 14px;
}
.book-quote {
    margin-top: 8px;
    font-style: italic;
    color: #555;
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
.voice-bad .voice-label {
    color: #dc2626;
}
.voice-good .voice-label {
    color: #16a34a;
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
.gold {
    color: #c9a227;
}
</style>
</head>
<body>
<div class="container">

<h1>BENSLEY CONTENT STRATEGY 2025</h1>

<div class="header-meta">
<strong>From:</strong> Lukas Sherman<br>
<strong>To:</strong> Bill Bensley, Brian Sherman<br>
<strong>Date:</strong> December 2025<br>
<strong>Subject:</strong> Content Strategy & Team Coordination Plan
</div>

<p class="intro">
Following our conversations about social media direction and the Bensley Brain, I've put together a comprehensive content strategy that consolidates everything we've discussed — your philosophy, the team structure, and how we're going to create content that actually matters.
</p>

<p class="intro">
<span class="highlight">The core shift: We're moving from showcasing Bensley to teaching Bensley.</span>
</p>

<p>Every piece of content should answer one question: <em>"What will someone learn from this that they'll remember in 5 years?"</em></p>

<blockquote>
"If it doesn't serve the planet or its people, then why bother? Every project I do has to earn its keep — protect a forest, create jobs, tell a story that matters. Otherwise, I'm out."
</blockquote>

<p>That's the standard we're holding all content to.</p>

<h2>THE THREE PILLARS</h2>

<p>All content maps to these pillars from your philosophy:</p>

<div class="pillar">
<h4>1. Truth to Place</h4>
<p>Nothing is designed "just because it looks good." Every decision is anchored in culture, climate, landscape, craft, and history. We start by visiting temples and heritage sites, reading deeply, speaking with locals — before we sketch.</p>
<blockquote>"With hotels, we have the wonderful opportunity to create an alternate universe for people."</blockquote>
</div>

<div class="pillar">
<h4>2. Sustainability & Stewardship</h4>
<p>No greenwashing. Real impact. Two key mantras:</p>
<ul>
<li><strong>"Minimal Intervention"</strong> — reading the lay of the land, building between or around trees rather than cutting them down</li>
<li><strong>"High Yield, Low Impact"</strong> — projects that give back more than they take</li>
</ul>
<blockquote>"My dream is to build a hotel made of 100% recycled materials... How cool would that be?"</blockquote>
</div>

<div class="pillar">
<h4>3. Joyful Originality</h4>
<blockquote>"Lebih gila, lebih baik — The crazier, the better. The odder, the better."</blockquote>
<p>The fantastical, theatrical elements that spark joy. No two Bensley properties are alike, yet the "Bensley vibe" is unmistakable: bold, witty, exuberant — and rigorously considered.</p>
</div>

<h2>THE TWO TRACKS</h2>

<p>I've restructured the team to have clear ownership:</p>

<div class="two-column">
<div class="column">
<h4>Track 1: Aubrey</h4>
<p><strong>In-House / Educational</strong></p>
<ul>
<li>Your knowledge & philosophy</li>
<li>Carousels with video hooks</li>
<li>Recurring series format</li>
</ul>
<p><em>"What Bill knows"</em></p>
</div>
<div class="column">
<h4>Track 2: Bani's Team</h4>
<p><strong>Field / Narrative</strong></p>
<ul>
<li>Projects, people, stories</li>
<li>Reels on location</li>
<li>Postcard Series + Quick Hits</li>
</ul>
<p><em>"What Bensley creates"</em></p>
</div>
</div>

<h2>TRACK 1: AUBREY — Educational Series</h2>

<h3>The Problem with the Current Approach</h3>

<p>Aubrey has been creating Reels that flip through 10+ items with captions — like the Science Fiction Books reel. While the content is great, <strong>cramming 10 books into one video is too hard to follow</strong>. You're skipping through so many different books with captions that it becomes overwhelming. No depth. Forgettable.</p>

<h3>The New Approach: Serialized Carousels with Depth</h3>

<p><strong>Format Structure:</strong></p>
<ul>
<li><strong>Slides 1-2:</strong> Engaging video or animation hook. Consistent visual identity.</li>
<li><strong>Slides 3-4:</strong> Your voiceover going deeper on <strong>1-2 items only</strong>. Real insight, not just a list.</li>
<li><strong>Remaining slides:</strong> Static with captions for context.</li>
<li><strong>Repeat:</strong> Next post continues the series (Books #3-4, etc.)</li>
</ul>

<p><strong>Why this works:</strong> Each post is digestible. Builds anticipation. Creates a recognizable visual identity. Content library grows over months.</p>

<h2>YOUR FAVORITES — The Content Library</h2>

<p>You've already provided rich commentary on your favorites. <span class="gold">This is gold.</span></p>

<h3>FAVORITE SCIENCE FICTION BOOKS</h3>

<blockquote>"I love books. Books feed the imagination, ignite the passions and stir emotions. Books for me are an endless source of ideas, creativity and new insights."<br>— BIBLIO BILL, Bangkok 2025</blockquote>

<div class="book-entry">
<div class="book-title">Parable of the Sower</div>
<div class="book-author">Octavia E. Butler</div>
<div class="book-quote">"I am inspired by Butler's vision of a dystopian future and the resilience of her protagonist."</div>
</div>

<div class="book-entry">
<div class="book-title">The Handmaid's Tale</div>
<div class="book-author">Margaret Atwood</div>
<div class="book-quote">"<strong>Atwood is my all-time favourite author.</strong> My hair stood on end when the Church of Reform elders began hanging homosexuals."</div>
</div>

<div class="book-entry">
<div class="book-title">The Three-Body Problem</div>
<div class="book-author">Cixin Liu</div>
<div class="book-quote">"Reading it feels like standing on the edge of the universe, pondering what might exist beyond our world."</div>
</div>

<div class="book-entry">
<div class="book-title">The Hunger Games</div>
<div class="book-author">Suzanne Collins</div>
<div class="book-quote">"This is a ridiculous book, especially the characters of the Capitol." <em>(Your honest take)</em></div>
</div>

<p><em>+ 7 more books with your commentary. We'll do 1-2 per carousel. Build the series over weeks.</em></p>

<h3>FAVORITE DESIGNERS</h3>

<p>Your origin story — this is content gold:</p>

<blockquote>
"Design has been in my blood since my early days at school. A talk by landscape architect Rocco Campanozzi triggered the lightbulb moment for me. On my invitation, he visited my high school one afternoon with a spectacular slide show of his work at Knotts Berry Farm. I knew I had to be a landscape architect. I was smitten, hook line and sinker. I am still in touch with Rocco to this day and often thank him for his time some 42 years ago now."
</blockquote>

<p><strong>The 20 Designers:</strong> David Collins, Geoffrey Bawa, Isamu Noguchi, Luis Barragan, Jaya Ibrahim, Frank Lloyd Wright, Antoni Gaudi, Michael Taylor, Ricardo Legoretta, Tony Duquette, Yabu + Pushelberg, Tony Chi, Ron Mann, Kit Kemp, Kelly Wearstler, Jeffrey Wilkes, John Saladino, Lek Bunnag, Jacques Garcia, Frank Gehry</p>

<h2>TRACK 2: BANI'S TEAM — Narrative Storytelling</h2>

<h3>TYPE A: POSTCARD SERIES (Deep-Dive Projects)</h3>

<p>In-depth storytelling about a specific Bensley project. The "Postcard" becomes a recognizable format.</p>

<p><strong>Blueprint:</strong></p>
<ol>
<li><strong>The Challenge</strong> — What was the site? What were the constraints?</li>
<li><strong>The Narrative</strong> — What story did we create?</li>
<li><strong>The Journey</strong> — Walk through the magic moments</li>
<li><strong>The Philosophy</strong> — End with the lesson ("The constraint became the magic")</li>
</ol>

<h3>THE SIAM POSTCARD</h3>

<p><strong>The Constraint:</strong> A narrow site near a busy road — but it goes into the river.</p>
<p><strong>The Solution:</strong> Pocket spaces. Their own unique places that open up to another pocket to another pocket.</p>
<p><strong>The Feeling:</strong> It's like a museum, but not a museum where you feel like you can't touch something — it's very homey and comfortable.</p>

<h3>INTERCON KHAO YAI POSTCARD (January Shoot)</h3>

<p><strong>The Narrative:</strong> The life of Som Sak, the train conductor.</p>
<p>All of the architecture, interiors, graphic design, signage, and storytelling is aligned to this one unique vision — connecting layout, typography, colors, and drawings with the narrative itself.</p>

<h3>FUTURE POSTCARDS</h3>

<table>
<tr><th>Project</th><th>The Story</th><th>Philosophy</th></tr>
<tr><td><strong>Four Seasons Koh Samui</strong></td><td>"We kept all 856 coconut trees. You wake up to monkeys, not marble lobbies."</td><td>Minimal Intervention</td></tr>
<tr><td><strong>Capella Ubud</strong></td><td>Zero trees cut. A 24-tent camp that "tip toes ever so softly on the land."</td><td>Constraint = Magic</td></tr>
<tr><td><strong>Shinta Mani Wild</strong></td><td>Zipline arrival. Guest stays fund anti-poaching rangers.</td><td>Purpose-Driven Design</td></tr>
</table>

<h3>TYPE B: QUICK HITS (Team & Process)</h3>

<p>Short, engaging Reels featuring real people sharing something interesting.</p>

<table>
<tr><th>Reel</th><th>Person</th><th>Status</th></tr>
<tr><td>P'Mum boat</td><td>P'Mum</td><td><span class="status-progress">In progress</span></td></tr>
<tr><td>Brian Siam walkthrough</td><td>Brian</td><td><span class="status-progress">In progress</span></td></tr>
<tr><td>Office Gatsby party</td><td>Team</td><td><span class="status-friday">Shoot: This Friday</span></td></tr>
<tr><td>Aubrey process</td><td>Aubrey</td><td>To shoot</td></tr>
</table>

<h2>THE BENSLEY VOICE</h2>

<div class="voice-comparison">
<div class="voice-box voice-bad">
<div class="voice-label">Not this (generic luxury)</div>
<p>"The resort features 50 luxuriously appointed villas with stunning ocean views and world-class amenities."</p>
</div>
<div class="voice-box voice-good">
<div class="voice-label">This (Bensley)</div>
<p>"We kept all 856 coconut trees at Four Seasons Koh Samui. The villas weave between them like they've always been there. You wake up to monkeys, not marble lobbies."</p>
</div>
</div>

<h2>QUOTABLE BILL — Ready for Content</h2>

<table>
<tr><th>Theme</th><th>Quote</th></tr>
<tr><td><strong>On Purpose</strong></td><td>"I'm done with designing hotels just to put heads on beds. Every project on our boards today has a purpose and a candle to light."</td></tr>
<tr><td><strong>On Creativity</strong></td><td>"The crazier, the better. The odder, the better."</td></tr>
<tr><td><strong>On Site Sensitivity</strong></td><td>"Minimal Intervention — reading the lay of the land."</td></tr>
<tr><td><strong>On Sustainability</strong></td><td>"High Yield, Low Impact. We want projects that give back more than they take."</td></tr>
<tr><td><strong>On Hotels</strong></td><td>"With hotels, we have the wonderful opportunity to create an alternate universe for people."</td></tr>
</table>

<div class="test-box">
<p>"Will someone remember this in 5 years?<br>Will it change how they think about design?"</p>
<p style="font-size: 14px; margin-top: 15px; font-style: normal;">If yes — publish. If no — rethink.</p>
</div>

<h2>DELIVERABLES</h2>

<h3>December (Now)</h3>
<ul>
<li>Gatsby party shoot <span class="status-friday">(Friday)</span></li>
<li>P'Mum boat Reel <span class="status-progress">(in progress)</span></li>
<li>Brian Siam walkthrough <span class="status-progress">(in progress)</span></li>
<li>The Siam Postcard intro Reel</li>
<li>Aubrey Quick Hit Reel</li>
<li>Begin Favorite Books carousel series (1-2 books per post)</li>
</ul>

<h3>January</h3>
<ul>
<li>InterCon Khao Yai shoot (Som Sak Postcard)</li>
<li>Continue Favorite Books series</li>
<li>Begin Favorite Designers series (with origin story as intro)</li>
<li>2x Quick Hit Reels (team members)</li>
</ul>

<h2>SUMMARY</h2>

<table class="summary-table">
<tr><th>Track</th><th>Owner</th><th>Format</th><th>Focus</th></tr>
<tr><td>Educational Series</td><td>Aubrey</td><td>Carousels</td><td>Your knowledge, favorites, philosophy</td></tr>
<tr><td>Narrative Storytelling</td><td>Bani's Team</td><td>Reels</td><td>Projects + People</td></tr>
</table>

<p><strong>The shift:</strong> From showcasing to teaching. From likes to lasting impact. From random posts to recognizable series.</p>

<p><strong>The goal:</strong> When someone follows Bensley, they learn something. When they think of design, they think of your philosophy. When they see a Bensley property, they understand WHY it feels different.</p>

<p>Everything feeds into the bigger picture: Instagram today, ESCAPISM 3 tomorrow, the Bensley Bible forever.</p>

<div class="footer">
<p>Let me know your thoughts on the direction.</p>
<p>Cheers,<br>Lukas</p>
</div>

</div>
</body>
</html>
"""

# Create email
msg = MIMEMultipart('alternative')
msg['From'] = smtp_user
msg['To'] = smtp_user
msg['Subject'] = "BENSLEY CONTENT STRATEGY 2025"

# Attach HTML
msg.attach(MIMEText(html_content, 'html'))

# Send
print(f"Sending HTML email via {smtp_host}...")

try:
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"TLS failed: {e}")
    print("Trying SSL on port 465...")
    try:
        with smtplib.SMTP_SSL(smtp_host, 465, timeout=30) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print("✅ Email sent successfully via SSL!")
    except Exception as e2:
        print(f"SSL also failed: {e2}")
