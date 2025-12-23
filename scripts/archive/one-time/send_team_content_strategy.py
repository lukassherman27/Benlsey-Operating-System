#!/usr/bin/env python3
"""
Send Team Content Strategy Email - HTML formatted
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
.example-box {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    padding: 20px;
    border-radius: 4px;
    margin: 20px 0;
}
.example-box h4 {
    margin-top: 0;
    color: #92400e;
}
.verdict {
    background: #f0fdf4;
    border: 2px solid #22c55e;
    padding: 15px;
    border-radius: 4px;
    text-align: center;
    font-weight: bold;
    color: #166534;
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

<p>This isn't about getting likes that vanish. It's about creating content that changes how people think about design.</p>

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

<h2>THE CONTENT TEST</h2>

<p>Before publishing anything, ask these questions:</p>

<div class="checklist">
<h4>1. Visual Check</h4>
<ul>
<li>Does this stop the scroll?</li>
<li>Is it visually distinctive (not generic hotel content)?</li>
<li>Does it have a recognizable Bensley aesthetic?</li>
</ul>
</div>

<div class="checklist">
<h4>2. Story Check</h4>
<ul>
<li>Is there a narrative arc (beginning &rarr; middle &rarr; end)?</li>
<li>Does it reveal something about HOW or WHY, not just WHAT?</li>
<li>Would someone want to share this with a friend?</li>
</ul>
</div>

<div class="checklist">
<h4>3. Insight Check</h4>
<ul>
<li>What's the one thing someone will remember?</li>
<li>Does it teach something about design/hospitality/creativity?</li>
<li>Does it align with Bill's philosophy?</li>
</ul>
</div>

<div class="checklist">
<h4>4. Pillar Check</h4>
<ul>
<li>Does it fit into Truth to Place, Sustainability, OR Joyful Originality?</li>
<li>Does it sound like Bill, not like generic luxury marketing?</li>
</ul>
</div>

<p><strong>If you can't check all boxes &rarr; rework it.</strong></p>

<h2>THE THREE PILLARS</h2>

<p>Every post should map to one of these:</p>

<div class="pillar">
<h4>1. Truth to Place</h4>
<blockquote>"With hotels, we have the wonderful opportunity to create an alternate universe for people."</blockquote>
<p>Nothing is designed "just because it looks good." Every decision is anchored in culture, climate, landscape, craft, and history.</p>
<p><strong>Content examples:</strong> Deep-dive project stories, site research process, the narrative behind a property (Som Sak at Khao Yai, the Opera at Capella Hanoi)</p>
</div>

<div class="pillar">
<h4>2. Sustainability & Stewardship</h4>
<blockquote>"High Yield, Low Impact. We want projects that give back more than they take."</blockquote>
<p>No greenwashing. Real impact. "Minimal Intervention" &mdash; reading the lay of the land, building around trees rather than cutting them down.</p>
<p><strong>Content examples:</strong> 856 coconut trees at Four Seasons Koh Samui, conservation rangers at Shinta Mani Wild, zero trees cut at Capella Ubud</p>
</div>

<div class="pillar">
<h4>3. Joyful Originality</h4>
<blockquote>"Lebih gila, lebih baik &mdash; The crazier, the better. The odder, the better."</blockquote>
<p>The fantastical, theatrical elements that spark joy. Bold, witty, exuberant &mdash; and rigorously considered.</p>
<p><strong>Content examples:</strong> Zipline arrival at Shinta Mani Wild, train carriages at InterCon Khao Yai, journey through pocket spaces at The Siam</p>
</div>

<h2>THE BENSLEY VOICE</h2>

<div class="two-column">
<div class="column">
<h4>DO:</h4>
<ul class="do-list">
<li>Challenge conventions: <em>"Why do hotel rooms all look the same?"</em></li>
<li>Celebrate nature: <em>"The jungle is the best architect"</em></li>
<li>Be playful: <em>"We don't do boring"</em></li>
<li>Use specific details: <em>"856 coconut trees"</em> not <em>"many trees"</em></li>
<li>End with philosophy, not features</li>
<li>Be passionate and direct</li>
</ul>
</div>
<div class="column">
<h4>DON'T:</h4>
<ul class="dont-list">
<li>Corporate speak</li>
<li>Generic hospitality clich&eacute;s (<em>"luxuriously appointed"</em>)</li>
<li>Overly formal tone</li>
<li>Ignore the environmental angle</li>
<li>List features without meaning</li>
</ul>
</div>
</div>

<h3>Voice Comparison</h3>

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

<h2>BILL'S CONTENT LIBRARY</h2>

<p>Bill has provided rich, detailed commentary we can use for months:</p>

<h3>Books & Authors</h3>
<table>
<tr><th>Series</th><th>Items</th><th>Bill's Commentary</th></tr>
<tr><td>Science Fiction Books</td><td>11 books</td><td>Full paragraph on each &mdash; why he loves it, what resonates</td></tr>
<tr><td>Fiction Books</td><td>9 books</td><td>Personal reflections, emotional responses</td></tr>
<tr><td>Mother Earth Books</td><td>5 books</td><td>Environmental philosophy connections</td></tr>
<tr><td>Books That Made Me Laugh</td><td>10 books</td><td>Personal stories, family connections</td></tr>
<tr><td>Adventure & Discovery</td><td>8 books</td><td>Explorer mindset, imagination</td></tr>
<tr><td>Extraordinary Prose</td><td>7 books</td><td>Writing craft, emotional impact</td></tr>
<tr><td>Stories of the Invincible</td><td>7 books</td><td>Courage, resilience themes</td></tr>
<tr><td>Most Treasured Authors</td><td>10 authors</td><td>Deep appreciation for each</td></tr>
</table>

<h3>Hotels & Places</h3>
<table>
<tr><th>Series</th><th>Items</th><th>Content Angle</th></tr>
<tr><td>Favourite Hotels (not Bensley)</td><td>9 hotels</td><td>What he admires, why they work</td></tr>
<tr><td>Favourite Hotels (Bensley)</td><td>12 properties</td><td>The story behind each, what makes it special</td></tr>
<tr><td>Best Places to Paint</td><td>Multiple</td><td>Creative inspiration, personal connection</td></tr>
<tr><td>Favourite Designers</td><td>20+</td><td>Origin story + why each inspires him</td></tr>
</table>

<h2>HOW TO PACKAGE THIS CONTENT</h2>

<h3>The Key Insight: Don't Cram</h3>

<p><strong>Old approach:</strong> 10 books in one video, flipping through with captions. Too fast. Forgettable.</p>

<p><strong>New approach:</strong> 1-2 items per post. Go deep. Build a series over time.</p>

<h3>Carousel Format (Aubrey)</h3>

<div class="format-box">
<span class="label">SLIDE 1-2: THE HOOK</span><br>
Video/animation that grabs attention<br>
Consistent visual identity so people recognize the series<br>
"BILL'S FAVORITE BOOKS #3" type branding<br><br>

<span class="label">SLIDE 3-4: THE DEPTH</span><br>
Bill's voiceover going deeper on ONE book<br>
His actual words, his perspective, his story<br>
This is where the INSIGHT lives<br><br>

<span class="label">SLIDE 5+: THE CONTEXT</span><br>
Static slides with key quotes, book covers<br>
Maybe a second book if closely related<br><br>

<span class="label">FINAL SLIDE: THE CTA</span><br>
"More next week" &mdash; builds anticipation<br>
Series continues, people come back
</div>

<h3>Reel Format (Bani)</h3>

<p><strong>Postcard Series (Project Deep-Dives)</strong> &mdash; Every project gets the same treatment:</p>

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

<p><strong>Quick Hits (Team & Process)</strong> &mdash; Short, human, authentic. Real people sharing something interesting.</p>

<h2>ANALYZING A CONTENT IDEA</h2>

<p>Use this framework before creating anything:</p>

<div class="example-box">
<h4>Example: "Carousel about Bill's favorite sci-fi books"</h4>

<p><strong>1. VISUAL &mdash; Is it stunning?</strong><br>
Can we create engaging visuals for book covers? What's the animation hook?<br>
<em>Answer:</em> Yes &mdash; stylized book covers, Bill-as-reader imagery, consistent format</p>

<p><strong>2. STORY &mdash; Is there narrative?</strong><br>
What's Bill's personal connection? Is there a "why" beyond just listing?<br>
<em>Answer:</em> Yes &mdash; each book has Bill's commentary about why it resonates</p>

<p><strong>3. INSIGHT &mdash; What do they learn?</strong><br>
Will someone discover something? Will they understand Bill's thinking?<br>
<em>Answer:</em> Yes &mdash; book recommendations + window into what shapes Bill's imagination</p>

<p><strong>4. PILLAR &mdash; Which one?</strong><br>
<em>Joyful Originality</em> &mdash; Bill's creative influences, imagination, curiosity</p>

<p><strong>5. VOICE &mdash; Does it sound like Bill?</strong><br>
Using his actual words? Personal, not generic? Specific details?<br>
<em>Answer:</em> Yes &mdash; direct quotes from his commentary</p>

<div class="verdict">&#10004; VERDICT: Proceed</div>
</div>

<h2>TWO TRACKS &mdash; WHO DOES WHAT</h2>

<div class="two-column">
<div class="column">
<h4>Track 1: Aubrey</h4>
<p><strong>Focus:</strong> Bill's knowledge, favorites, philosophy</p>
<p><strong>Format:</strong> Carousels with video/animation hooks</p>
<p><strong>Theme:</strong> "What Bill knows"</p>
<ul>
<li>Favorite Books series</li>
<li>Favorite Designers series</li>
<li>Philosophy Quotes</li>
<li>Design Tips</li>
</ul>
</div>
<div class="column">
<h4>Track 2: Bani</h4>
<p><strong>Focus:</strong> Projects, people, process</p>
<p><strong>Format:</strong> Reels on location</p>
<p><strong>Theme:</strong> "What Bensley creates"</p>
<ul>
<li>Postcard Series (project deep-dives)</li>
<li>Quick Hits (team moments)</li>
</ul>
</div>
</div>

<h2>POSTING SCHEDULE</h2>

<p><strong>Target: 3-4 posts per week</strong></p>

<table>
<tr><th>Day</th><th>Content Type</th><th>Track</th></tr>
<tr><td>Monday</td><td>Philosophy quote</td><td>Aubrey</td></tr>
<tr><td>Wednesday</td><td>Educational carousel</td><td>Aubrey</td></tr>
<tr><td>Friday</td><td>Reel (Postcard or Quick Hit)</td><td>Bani</td></tr>
<tr><td>Sunday</td><td>Behind-the-scenes / teaser</td><td>Either</td></tr>
</table>

<h2>COORDINATION WORKFLOW</h2>

<h3>For Carousels (Aubrey)</h3>
<div class="workflow-box">
<span class="day">MONDAY:</span> Lukas sends brief (topic, Bill's quotes, visual direction)<br>
<span class="day">TUES-WED:</span> Aubrey creates draft (hook + content + CTA slides)<br>
<span class="day">THURSDAY:</span> Review & feedback, adjustments made<br>
<span class="day">FRIDAY:</span> Bill approves, schedule for posting
</div>

<h3>For Reels (Bani)</h3>
<div class="workflow-box">
<span class="day">WEEK BEFORE:</span> Lukas sends brief (story structure, key shots, Bill quotes)<br>
<span class="day">SHOOT DAY:</span> Capture B-roll, walking shots, detail moments<br>
<span class="day">POST-SHOOT:</span> Rough cut &rarr; feedback &rarr; final edit<br>
<span class="day">APPROVAL:</span> Lukas reviews, Bill approves, post
</div>

<h2>WHAT SUCCESS LOOKS LIKE</h2>

<p>We'll know this is working when:</p>
<ol>
<li><strong>People remember</strong> &mdash; They can recall what they learned from a post</li>
<li><strong>People share</strong> &mdash; They send content to friends with "you need to see this"</li>
<li><strong>People engage</strong> &mdash; Comments are about the IDEAS, not just "beautiful!"</li>
<li><strong>Growth happens</strong> &mdash; Follower count increases because content has value</li>
<li><strong>Consistency holds</strong> &mdash; 3-4x/week posting rhythm is sustained</li>
</ol>

<h2>IMMEDIATE PRIORITIES</h2>

<h3>This Week</h3>
<ul>
<li>Gatsby party shoot &mdash; elegant, not whacky</li>
<li>Create carousel template &mdash; consistent format for Bill's Favorites series</li>
<li>Draft first Books carousel (Books #1-2)</li>
</ul>

<h3>January</h3>
<ul>
<li>Launch Favorite Books series</li>
<li>Launch Favorite Designers series (origin story first)</li>
<li>Confirm InterCon Khao Yai shoot date</li>
<li>Complete P'Mum + Brian reels</li>
</ul>

<div class="test-box">
<p>"Will someone remember this in 5 years?<br>Will it change how they think about design?"</p>
<p class="subtext">If yes &rarr; publish | If no &rarr; rework</p>
</div>

<h2>SUMMARY</h2>

<table class="summary-table">
<tr><th>Track</th><th>Person</th><th>Format</th><th>Focus</th></tr>
<tr><td>Educational</td><td>Aubrey</td><td>Carousels</td><td>Bill's knowledge, favorites, philosophy</td></tr>
<tr><td>Narrative</td><td>Bani</td><td>Reels</td><td>Projects, people, process</td></tr>
</table>

<p style="margin-top: 30px; text-align: center;">
<strong>The shift:</strong> From showcasing to teaching<br>
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
msg['Subject'] = "BENSLEY Content Strategy - Team Guide"

# Attach HTML
msg.attach(MIMEText(html_content, 'html'))

# Send
print(f"Sending Content Strategy to {smtp_user}...")

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
