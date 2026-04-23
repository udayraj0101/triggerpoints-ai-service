TriggerPoints3D AI Chatbot – Final Specification (Corrected Navigation Logic)

1. Core Principle
The chatbot must:
Understand user intent
Identify muscle or symptom
Decide response type:
Text (from PDF via RAG)
Navigation (guide inside app)
Hybrid (text + navigation)

2. Navigation Model (Critical Update)
There are two valid navigation flows and chatbot must choose based on user intent.

FLOW A — Symptom-Based Navigation (When user does NOT know muscle)
Use this when:
User mentions symptom
User asks “which muscle causes…”
User is unsure about muscle

Steps:
Go to Symptoms screen
Select body region
Select symptom
App shows:
Primary muscles
Secondary muscles
User selects a muscle
App opens split view (landscape mode automatically)

FLOW B — Direct Muscle Navigation (When user KNOWS muscle)
Use this when:
User mentions a specific muscle
User asks to see pain map / trigger points / video / self-help

Steps:
Tap the rotate/switch button
App enters landscape mode
Split view opens:
Left: pain map
Right: trigger points
Select body region on the right navigation
Search/select the muscle


3. Navigation Rules (Decision Logic)

Rule 1 — If user provides a symptom
Example:
"I have cheek pain"
→ Use FLOW A

Rule 2 — If user provides a muscle
Example:
"Show Digastricus pain map"
→ Use FLOW B

Rule 3 — If user asks “which muscle…”
Example:
"Which muscle causes dizziness?"
→ First show muscles (TEXT)
→ Then suggest FLOW A

Rule 4 — If user asks for visual (pain map / trigger points / video / self-help)
→ Always use FLOW B if muscle is known
→ Else use FLOW A

4. Navigation Instruction Engine (FINAL VERSION)

4.1 Pain Map Navigation

Case 1 — Muscle Known (FLOW B)
To view the pain map:
Tap the rotate/switch button to enter landscape mode
Select the body region
Search and select the muscle
The pain map will be visible on the left side

Case 2 — Muscle Unknown (FLOW A)
To view the pain map:
Go to the Symptoms screen
Select body region
Select symptom
Select a muscle from the list
The split view will open
Pain map is shown on the left

4.2 Trigger Points Navigation

Muscle Known (FLOW B)
Tap rotate/switch button to enter landscape mode
Select body region
Select the muscle
Trigger points appear on the right side (blue dots)

Muscle Unknown (FLOW A)
Go to Symptoms screen
Select body region
Select symptom
Select muscle
Trigger points appear on right side

4.3 Video Navigation

Muscle Known (FLOW B)
Tap rotate/switch button to enter landscape mode
Select body region
Select the muscle
Tap the Play button
Choose video type:
Safety
Needling
Functional Anatomy
TP Overview

Muscle Unknown (FLOW A)
Go to Symptoms screen
Select body region
Select symptom
Select muscle
Tap Play button
Choose video

4.4 Self-Help and Advice Navigation (IMPORTANT – CORRECTED)
This must ALWAYS follow landscape flow.

Final Correct Flow (as per your app):
Tap the rotate/switch button to enter landscape mode
Select the body region
Search and select the muscle
In split view, locate the Self Help and Advice button (bottom right)
Tap it to view:
Causes
Advice
Techniques

If user does NOT know muscle:
Go to Symptoms screen
Select body region
Select symptom
Select muscle
App opens split view
Tap Self Help button (bottom right)

5. Hybrid Response Logic
When both explanation and navigation are useful:
Example:
"How to treat SCM trigger points?"
Response:
Short explanation (from PDF)
Then navigation (FLOW B)

6. Decision Engine (Final Logic)

IF query contains symptom:
→ return muscles
→ suggest FLOW A

IF query contains muscle:
IF visual intent:
    → use FLOW B

ELSE:
    → return TEXT (RAG)


IF query contains both:
→ return TEXT + FLOW B

IF query asks how to use app:
→ return navigation steps

7. Entity Detection

Muscle Detection
Exact match
Fuzzy match
Alias match (e.g. SCM)
Return:
muscle
body region

Symptom Detection
Match from symptoms table

8. Context Memory
Store:
last muscle
last symptom

Example:
User:
"I have neck pain"
User:
"Show video"
→ System uses last symptom → FLOW A

9. Sample User Queries (Updated)

Muscle Known → Direct Flow
Show pain map of Digastricus
Show trigger points of SCM
Show video for Deltoid
Open self help for Quadratus Lumborum
Where is Gastrocnemius muscle

Symptom Based → Flow A
I have cheek pain
Pain at back of neck
Dizziness
Lower back pain

Hybrid
How to treat SCM trigger points
Explain Digastricus and show pain map
What causes cheek pain and how to fix it

App Help
How do I see pain map
How do I view trigger points
How to watch videos
How to use self help

10. Final Expected Behavior
The chatbot must:
Identify if user knows muscle or not
Choose correct navigation flow
Avoid forcing Symptoms screen
Prefer direct landscape flow when muscle is known
Provide clear, step-by-step instructions
Combine text + navigation when needed

11. Implementation Priority
Database setup
Muscle + symptom mapping
Intent detection
Navigation engine (with dual flow)
RAG system
