# AI Math Shorts Factory — Local-First Architecture & Build Plan

## 1. Goal

Build a **locally hosted, continuously running AI production system** that generates, validates, previews, approves, renders, and uploads 60-second Manim-based math videos for:

1. **University-level mathematics explained visually**
2. **Maths for AI explained for everyone**

The system must support two content modes:

- **Theory mode**: concept-first, proof-flavored, deep insight, intuition, precise mathematics
- **Application mode**: concept + why it matters + where it appears in AI / science / engineering

It must:

- run **24/7** once started
- propose new ideas **without waiting for manual prompting**
- use **free / locally hostable tools** where possible
- use **Manim** for visuals
- include **narration** and **background music**
- be **strictly source-grounded** in trustworthy academic references
- require **manual approval** at these gates:
  1. idea approval
  2. script approval
  3. final video approval
  4. upload approval
- support **parallel work** on different videos and stages
- expose a **local web dashboard** for queue state, previews, approvals, logs, and failures
- automatically **quality-check Manim layouts** for overlap / cramped spacing and repair them
- allow feedback-driven workflow expansion, but only **after your approval**

---

## 2. Product Vision

Think of the system as a **video factory with human editorial checkpoints**.

It should behave like this:

1. Continuously discover candidate topics from a curated topic pool.
2. Rank topics by educational value, novelty, visual potential, and fit for 60-second format.
3. Draft a grounded idea card with academic references.
4. Wait for your approval.
5. Draft a short script and scene plan, still source-grounded.
6. Wait for your approval.
7. Generate Manim code, narration, subtitles, metadata, thumbnails, and final vertical video.
8. Run visual QA and audio/video QA.
9. Wait for your approval.
10. Upload to YouTube Shorts and Instagram Reels.
11. Wait for your approval before publishing.
12. Log performance data and feed it back into future topic selection.

The pipeline should never silently publish. It should always stop at the defined approval gates.

---

## 3. Hard Constraints

### 3.1 Content constraints

- Every factual mathematical claim must be traceable to one or more academic references.
- The script must separate:
  - **verbatim claims from sources**
  - **derived explanations / simplifications**
  - **visual metaphors**
- Every generated asset must carry provenance metadata internally:
  - source DOI / URL / title / authors
  - claim-to-source mapping
  - generation model + version
  - prompt + revision history

### 3.2 Style constraints

Aim for a **clean mathematical animation style inspired by rigorous explainer channels**, but do **not** hard-code imitation of any one creator. Encode the style as:

- dark background
- high contrast typography
- limited palette
- slow camera movement
- strong geometric composition
- sparse screen density
- one key idea at a time
- fewer words, more motion
- clear progression: hook -> intuition -> core statement -> consequence

### 3.3 Operational constraints

- Must run locally with Docker Compose.
- Must tolerate restarts.
- Must persist state in a database.
- Must support multiple workers.
- Must be resumable from any failed step.
- Must never lose approval state or source-traceability records.

---

## 4. Recommended Stack

## 4.1 Core application

- **Backend API**: FastAPI
- **Task queue**: Celery
- **Broker**: Redis
- **Database**: PostgreSQL
- **Frontend dashboard**: Next.js or React + Vite
- **Realtime updates**: WebSocket / Server-Sent Events
- **Object storage**: local filesystem first, optionally MinIO
- **Auth**: single-user local auth initially, later role-based auth

### Why this stack

- FastAPI is clean for orchestration, APIs, and internal services.
- Celery + Redis gives robust parallel job execution.
- PostgreSQL is the source of truth for workflow state and approvals.
- React/Next.js is ideal for dashboard, previews, and review UI.
- Docker Compose makes the whole system locally reproducible.

---

## 4.2 AI / media toolchain

### Planning and code generation

- **Claude Code** as the main coding / orchestration assistant during development
- **Ollama** for locally served open models
- Suggested local models by role:
  - topic ideation / summarisation: medium instruct model
  - script writing: stronger reasoning/instruct model
  - code generation for Manim: coder model
  - critique / evaluator: separate reviewer model

### Academic sourcing

- Crossref API for bibliographic metadata
- Semantic Scholar API for discovery / citation graph / relevance expansion
- arXiv ingestion for preprints where appropriate
- manual allowlist of trusted textbooks, lecture notes, surveys, and papers

### Math / verification

- Python
- SymPy
- mpmath
- NumPy
- optional SciPy

### Animation and composition

- Manim Community Edition
- FFmpeg for muxing, scaling, audio mixing, subtitles burn-in, thumbnail extraction

### Narration

- Local open-source TTS (primary): **Coqui TTS / XTTS-compatible setup**
- fallback: Piper for lightweight fully local voices

### Speech / subtitle QA

- faster-whisper for local transcription and alignment checks

### Browser automation / screenshots

- Playwright for dashboard testing, preview snapshots, and optional upload fallbacks if an API is unavailable

---

## 5. External platform reality you must design around

### YouTube

YouTube video upload is available through the YouTube Data API. However, uploads from **unverified API projects created after 28 July 2020 are restricted to private viewing mode** until the project passes audit, so your system should treat this as expected behavior during development. Design the upload service to support **private -> manual review -> metadata update -> publish**. 

### Instagram

Instagram publishing should be treated as a **capability-checked integration**, not a guaranteed step for every account. Reels publishing is supported through the Instagram Graph API for eligible business/creator setups, with the right app permissions and account linkage. The system must therefore include an **account readiness check** before enabling automatic upload flow.

### Consequence for architecture

Your upload module should expose:

- `youtube_enabled`
- `instagram_enabled`
- `youtube_account_ready`
- `instagram_account_ready`
- `reels_publish_supported`

If an integration is not ready, the workflow should stop at **Upload Pending** with exact remediation instructions.

---

## 6. System architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Local Web Dashboard                     │
│ queue │ jobs │ approvals │ preview │ logs │ settings │ QA │
└───────────────▲───────────────────────▲────────────────────┘
                │                       │
                │ REST / WS             │ review actions
                │                       │
┌───────────────┴───────────────────────┴────────────────────┐
│                      FastAPI Control Plane                 │
│  workflow API │ approval API │ asset API │ metrics API    │
│  scheduler    │ policy engine │ source registry │ auth     │
└──────▲──────────────▲──────────────▲──────────────▲────────┘
       │              │              │              │
       │ DB           │ queue        │ files        │ events
       │              │              │              │
┌──────┴──────┐ ┌─────┴─────┐ ┌─────┴────────┐ ┌───┴────────┐
│ PostgreSQL  │ │   Redis   │ │ Asset Store  │ │ Event Bus  │
│ workflow    │ │ Celery    │ │ renders/audio│ │ internal    │
│ approvals   │ │ broker    │ │ manifests    │ │ notifications│
└──────▲──────┘ └─────▲─────┘ └─────▲────────┘ └───▲────────┘
       │              │              │              │
       └───────┬──────┴─────┬────────┴───────┬──────┘
               │            │                │
      ┌────────┴───┐ ┌──────┴─────┐ ┌────────┴────────┐
      │ Research    │ │ Script/Plan│ │ Manim Generator │
      │ workers     │ │ workers    │ │ workers         │
      └────────▲────┘ └──────▲─────┘ └────────▲────────┘
               │             │                │
      ┌────────┴────┐ ┌──────┴──────┐ ┌───────┴────────┐
      │ Verification │ │ Narration   │ │ Render / QA    │
      │ math workers │ │ TTS workers │ │ workers         │
      └────────▲─────┘ └──────▲──────┘ └───────▲────────┘
               │              │                │
               └──────┬───────┴───────┬────────┘
                      │               │
               ┌──────┴──────┐ ┌──────┴──────┐
               │ Packaging    │ │ Upload      │
               │ workers      │ │ workers     │
               └──────────────┘ └─────────────┘
```

---

## 7. Workflow model

Represent each video as a **state machine**.

### 7.1 Top-level states

1. `DISCOVERED`
2. `IDEA_DRAFTED`
3. `WAITING_IDEA_APPROVAL`
4. `SCRIPT_DRAFTED`
5. `WAITING_SCRIPT_APPROVAL`
6. `ASSETS_GENERATING`
7. `MANIM_QA`
8. `AUDIO_QA`
9. `FINAL_COMPOSED`
10. `WAITING_FINAL_APPROVAL`
11. `READY_TO_UPLOAD`
12. `WAITING_UPLOAD_APPROVAL`
13. `UPLOADING`
14. `PUBLISHED`
15. `REJECTED`
16. `REVISION_REQUESTED`
17. `FAILED`
18. `ARCHIVED`

### 7.2 Parallelisable subjobs

A single video can fan out into parallel tasks after script approval:

- Manim scene generation
- citation pack generation
- narration generation
- subtitle generation
- thumbnail generation
- metadata generation
- music selection / trimming
- QA screenshot generation

This is the main lever for throughput.

---

## 8. Approval design

Approval is not an afterthought. It is a first-class workflow primitive.

### 8.1 Approval gates

#### Gate A — Idea approval
Review card shows:

- working title
- category: theory / application
- audience level
- one-sentence hook
- 60-second structure
- why this topic fits short-form
- key claims
- academic references
- expected visual motifs
- expected difficulty / risk

Actions:

- Approve
- Reject
- Ask for revision
- Ask for variant ideas

#### Gate B — Script approval
Review page shows:

- full voiceover script
- scene-by-scene timing
- source-to-claim map
- risky simplifications highlighted
- narration length estimate
- visual density estimate

Actions:

- Approve
- Reject
- Annotate problems
- Ask for shorter / more rigorous / more visual revision

#### Gate C — Final product approval
Review page shows:

- MP4 preview
- captions preview
- waveform
- narration transcript
- scene screenshots
- QA warnings
- citation pack

Actions:

- Approve
- Reject
- Request fix with free-text issue report

#### Gate D — Upload approval
Review page shows:

- platform targets
- title
- description
- hashtags
- thumbnail
- upload status precheck
- privacy state

Actions:

- Approve upload
- Reject upload
- Publish only to selected platforms

### 8.2 Revision handling

If rejected, the system asks for structured feedback:

- mathematical issue
- visual issue
- pacing issue
- tone issue
- narration issue
- citation/source issue
- platform formatting issue
- other

It then creates a **revision brief** and resumes from the lowest necessary stage, not from scratch.

---

## 9. Source-grounding subsystem

This is the most important trust layer.

### 9.1 Source policy

Allow only:

- peer-reviewed papers
- standard textbooks
- trusted university lecture notes
- authoritative surveys
- official documentation for technical tooling

Disallow as primary math sources:

- random blogs
- unsourced explainers
- social media posts
- LLM-generated claims without source backing

### 9.2 Internal source entities

#### SourceRecord
- id
- title
- authors
- year
- DOI
- URL
- source_type
- publisher / journal
- abstract
- trust_score
- retrieved_at
- checksum

#### ClaimRecord
- id
- video_id
- claim_text
- claim_type (`definition`, `theorem`, `intuition`, `historical`, `application`, `analogy`)
- confidence
- review_status

#### ClaimSourceLink
- claim_id
- source_id
- evidence_snippet
- page_numbers
- support_type (`direct`, `derived`, `contextual`)

### 9.3 Citation workflow

1. Topic planner proposes candidate claims.
2. Research worker retrieves sources.
3. Claim linker maps each claim to sources.
4. Verifier flags unsupported claims.
5. Script writer can only use supported claims.
6. Final artifact stores citation pack in JSON.

### 9.4 Trust scoring

Rank sources by weighted score:

- textbook / peer-reviewed / survey bonus
- citation count bonus
- recent survey bonus
- university publisher bonus
- duplicate corroboration bonus
- preprint penalty unless corroborated
- blog penalty

Use at least **two independent sources** for core claims where feasible.

---

## 10. Topic discovery engine

Since the tool must start generating ideas by itself, create a dedicated topic engine.

### 10.1 Topic pools

#### University maths pool
- linear algebra
- real analysis
- abstract algebra
- complex analysis
- probability
- topology (selective)
- differential equations
- optimization
- information theory foundations

#### Maths for AI pool
- gradients
- chain rule
- Jacobians
- Hessians
- eigenvectors / PCA
- SVD
- convolution
- Fourier transform intuition
- probability distributions
- KL divergence
- cross entropy
- softmax
- attention
- optimisation / gradient descent

### 10.2 Topic card schema

- topic
- subtopic
- type: theory/application
- audience
- prerequisite level
- visual richness score
- novelty score
- short-form suitability score
- reference pack
- prior coverage score

### 10.3 Scheduling logic

Use a weighted scheduler to avoid repetition:

`priority = freshness + visual_score + educational_value + channel_strategy - repetition_penalty - complexity_penalty`

### 10.4 Anti-redundancy policy

Do not generate two very similar videos in close succession.

Maintain embeddings + tag similarity against:

- approved ideas
- completed videos
- rejected topics

---

## 11. Script generation architecture

Generate scripts in layers, not one shot.

### 11.1 Layered script pipeline

1. `research_brief`
2. `claim_graph`
3. `hook_options`
4. `short_script_v1`
5. `timing_pass`
6. `rigour_pass`
7. `voice_pass`
8. `source_check_pass`

### 11.2 60-second script template

```text
0–5s    Hook
5–15s   Define the concept visually
15–35s  Core intuition / statement
35–50s  Proof sketch or application insight
50–60s  Closing payoff / curiosity loop
```

### 11.3 Script constraints

- target spoken length: 130–155 words
- max on-screen text density threshold
- one theorem-like object per short unless extremely simple
- no more than 3 major visual motifs
- every sentence tagged with scene id
- every claim tagged with source ids

### 11.4 Reviewer passes

Run separate reviewer prompts for:

- mathematical correctness
- pedagogy for target audience
- visual filmability in Manim
- timing
- jargon overload
- unsupported claims

Only promote script if all passes are green.

---

## 12. Scene planning and Manim generation

Do not ask the code generator to “make a video”. Give it a strong intermediate representation.

### 12.1 Scene Manifest (`scene_manifest.json`)

Each scene should contain:

- `scene_id`
- `start_time_estimate`
- `duration_estimate`
- `voiceover_lines`
- `math_objects`
- `text_objects`
- `visual_goal`
- `animation_sequence`
- `layout_constraints`
- `qa_targets`
- `source_claim_ids`

### 12.2 Reusable Manim primitives

Build a library of composable components:

- `TitleCard`
- `EquationBuild`
- `DefinitionBox`
- `ProofSketchBox`
- `VectorFieldPanel`
- `MatrixTransformPanel`
- `ProbabilityBar`
- `LossLandscapePanel`
- `GradientArrowField`
- `AxesPlotPanel`
- `NeuralNetBlock`
- `CalloutLabel`
- `CaptionStrip`
- `HookFrame`
- `EndCard`

### 12.3 Manim code generation policy

The generator should produce:

- one Python file per video
- one scene class per logical scene
- a shared style config import
- no magic numbers unless justified
- all positions derived from layout helpers
- all displayed text from the approved scene manifest

### 12.4 Safe layout helpers

Create internal layout helpers such as:

- `safe_arrange(mobjects, direction, buff, edge_padding)`
- `safe_stack(groups, min_vertical_gap)`
- `fit_to_vertical_frame(mobject, top_margin, bottom_margin)`
- `keep_clear_of_caption_zone(mobject)`
- `align_equation_and_label(eq, label, min_gap)`
- `auto_shrink_text(text_obj, max_width, min_font_size)`

Never place objects by arbitrary hand-tuned coordinates unless wrapped in a helper.

---

## 13. Automatic visual QA for Manim

You explicitly want the pipeline to detect overlapping objects and cramped spacing, then repair them.

Implement this as a real subsystem, not a vague “LLM review”.

### 13.1 QA stages

#### Stage 1 — Static scene geometry check
For each rendered keyframe or scene state, compute bounding boxes for all visible objects.

Check:

- object intersection area > threshold
- line spacing below threshold
- text too close to frame edge
- text entering caption-safe area
- object crowding density too high
- small font below readability threshold
- arrows / labels too close

#### Stage 2 — Screenshot-based visual review
Render scene snapshots and run a vision review step to detect:

- clutter
- unreadable text
- imbalance
- visual dead zones
- accidental overlay with subtitle region

#### Stage 3 — Auto-repair
If overlap or crowding is found, apply deterministic repair rules first:

1. increase `buff`
2. increase vertical gaps
3. shrink font within limits
4. split one dense scene into two scenes
5. move non-essential annotation to next beat
6. abbreviate on-screen text while leaving narration unchanged

Only after deterministic repair fails should an LLM propose a layout patch.

### 13.2 Geometry QA algorithm

For each frame snapshot:

1. Extract visible Manim mobjects.
2. Compute bounding box in screen coordinates.
3. Ignore whitelisted overlaps (e.g. label intentionally attached to object).
4. For all other pairs:
   - compute IoU
   - compute min distance
5. For text groups:
   - compute baseline spacing
   - compare against typography thresholds
6. Produce QA issue list.

### 13.3 Example thresholds

- object IoU must be near zero unless explicitly allowed
- min object gap: 16 px equivalent
- line gap: >= 1.2 x font height
- edge padding: >= 5% frame width/height
- subtitle-safe bottom margin: reserved region
- max words on screen at once: configurable

### 13.4 Auto-fix loop

```text
generate scene layout
-> static QA
-> if fail, repair layout
-> rerender preview frame
-> screenshot QA
-> if fail, repair again
-> if still fail after N rounds, escalate to manual review
```

### 13.5 Logging

Every repair attempt should be logged with:

- original metric
- patched parameter
- result metric
- accepted / rejected outcome

This becomes training data for later improvements.

---

## 14. Narration subsystem

### 14.1 Requirements

- free or fully local
- deterministic voice choice per channel / series
- configurable speaking rate
- sentence-level timestamp alignment

### 14.2 Pipeline

1. approved script
2. pronunciation normalization pass
3. TTS synthesis
4. loudness normalization
5. silence trimming
6. transcript alignment with faster-whisper
7. mismatch detection

### 14.3 Mismatch checks

Reject narration if:

- missing sentence
- hallucinated word insertion
- pronunciation is unacceptable for core terms
- duration is too long for 60-second cut

### 14.4 Voice policy

Store several voice profiles:

- formal maths explainer
- friendly AI explainer
- concise short-form narrator

---

## 15. Background music subsystem

### 15.1 Requirements

- free to use under the chosen workflow
- locally stored
- low distraction
- loopable and level-controlled

### 15.2 Design

Maintain a curated local library tagged by:

- energy
- mood
- tempo
- density
- best for theory/application

Automatically select BGM by script mood and pacing.

### 15.3 Audio mix rules

- narration is always dominant
- duck music under speech
- music intro/outro fade
- no sudden cuts
- LUFS targets configurable

---

## 16. Final composition

### 16.1 Target format

For Shorts/Reels primary output:

- 1080x1920 vertical
- 60 seconds max
- H.264 MP4
- captions optional burn-in and separate subtitle track where useful

### 16.2 Composition steps

1. concatenate Manim renders
2. add narration
3. add BGM with ducking
4. add captions / subtitles
5. add intro/outro if enabled
6. normalize final audio
7. render preview MP4
8. render final MP4
9. extract thumbnail candidate frames

### 16.3 Deliverables per video

- final video
- preview video
- subtitles
- narration wav
- clean music-mixed wav
- thumbnail candidates
- citation pack JSON
- source manifest JSON
- scene manifest JSON
- logs

---

## 17. Upload subsystem

### 17.1 Platform abstraction

Create a common interface:

```python
class PlatformPublisher:
    def precheck(self, account_id): ...
    def upload(self, asset_bundle, metadata): ...
    def poll_status(self, upload_id): ...
    def publish(self, upload_id): ...
```

Implement:

- `YouTubePublisher`
- `InstagramPublisher`

### 17.2 YouTube flow

- create upload metadata
- upload video
- set title/description/tags/privacy
- optionally set thumbnail
- record returned platform ids

### 17.3 Instagram flow

- precheck eligible account
- create media container
- publish reel
- poll processing state
- record returned ids and errors

### 17.4 Safe publication policy

Upload approval should allow:

- both platforms
- YouTube only
- Instagram only
- save metadata draft only

---

## 18. Continuous scheduler / 24-7 autonomy

You want the pipeline to start generating without being manually told each time.

### 18.1 Supervisor loop

Run a daemon that always tries to keep the factory stocked.

Example target buffers:

- 5 ideas waiting for review
- 3 scripts waiting for review
- 2 finals waiting for review
- 1 upload-ready video queued

### 18.2 Scheduler responsibilities

- replenish idea queue
- honour concurrency limits
- avoid topic duplication
- requeue failed resumable jobs
- pause categories if too many rejects
- throttle GPU-heavy tasks if resources are constrained

### 18.3 Autonomy boundary

The system is autonomous for **generation**, but not for **approval-gated transitions**.

It can keep working on other videos while one video waits for your decision.

---

## 19. Dashboard design

### 19.1 Pages

#### Home dashboard
- system status
- workers online
- GPU/CPU/memory
- queue counts by stage
- recent failures
- latest approvals needed

#### Pipeline board
Kanban-like columns:
- idea drafting
- waiting idea approval
- script drafting
- waiting script approval
- rendering
- QA
- waiting final approval
- waiting upload approval
- published

#### Video detail page
- metadata
- topic tags
- current state
- all assets
- logs
- approvals history
- source pack
- revision history

#### Preview page
- embedded video player
- timeline screenshots
- subtitles panel
- source map panel
- approve/reject buttons

#### Research page
- source documents
- extracted claims
- citation graph
- trust scores

#### Settings page
- tools paths
- model choices
- account integrations
- channel style rules
- safety thresholds
- upload defaults

### 19.2 Rejection UX

When you reject, require structured feedback plus optional free text.

The system should convert this into a revision ticket with:

- severity
- component owner
- rollback stage
- acceptance criteria

---

## 20. Database design

Core tables:

- `videos`
- `video_versions`
- `workflow_runs`
- `jobs`
- `approvals`
- `revision_requests`
- `sources`
- `claims`
- `claim_source_links`
- `scene_manifests`
- `asset_files`
- `qa_reports`
- `platform_accounts`
- `platform_uploads`
- `system_settings`
- `events`

### 20.1 Critical entities

#### videos
- id
- slug
- title
- topic
- content_type
- audience
- status
- current_version_id
- created_at
- updated_at

#### approvals
- id
- video_id
- gate_type
- status
- reviewer
- notes
- created_at
- decided_at

#### qa_reports
- id
- video_id
- qa_type
- status
- metrics_json
- issues_json
- repair_actions_json
- created_at

---

## 21. Filesystem layout

```text
project/
  apps/
    api/
    web/
    worker/
  packages/
    core/
    prompts/
    schemas/
    manim_lib/
    publishers/
    qa/
    research/
    tts/
  infra/
    docker/
    scripts/
    nginx/
  data/
    postgres/
    redis/
    assets/
    models/
    music/
    caches/
    uploads/
  runs/
    <video_id>/
      idea/
      research/
      script/
      scenes/
      manim/
      audio/
      qa/
      final/
      upload/
  docs/
    architecture/
    prompts/
    ops/
  tests/
    unit/
    integration/
    e2e/
```

---

## 22. Bootstrapping and automatic tool download

You asked that free tools be downloaded automatically before running.

### 22.1 Bootstrap strategy

Create a `bootstrap.py` or shell installer that:

1. checks OS
2. checks Python / Docker / GPU capability
3. installs system dependencies
4. downloads required models and tools
5. validates executables
6. warms caches
7. writes local config
8. launches Docker Compose

### 22.2 Bootstrap targets

- Manim and LaTeX dependencies
- FFmpeg
- Ollama
- selected local models
- Coqui TTS or Piper assets
- faster-whisper model
- Playwright browsers
- Python dependencies

### 22.3 Important caveat

Some “free” tools are free but not identical in license, redistribution, or model-weight availability. Therefore the bootstrap phase should have a **license check panel** that clearly marks:

- installable automatically
- requires manual acceptance
- optional component

Do not hardwire everything into silent download scripts.

---

## 23. Concurrency model

### 23.1 Worker pools

Use specialised queues:

- `research_queue`
- `planning_queue`
- `script_queue`
- `manim_queue`
- `audio_queue`
- `qa_queue`
- `compose_queue`
- `upload_queue`

### 23.2 Resource-aware scheduling

Not all tasks should run equally in parallel.

Example policy:

- many research/script tasks in parallel on CPU
- limited number of Manim renders
- limited number of TTS tasks
- only one or two final FFmpeg encodes per GPU/CPU target

### 23.3 Locking

Use DB row locks or Redis locks for:

- approval transitions
- video version promotion
- upload deduplication
- revision state changes

---

## 24. Feedback-driven workflow evolution

You asked for the pipeline to add steps if your feedback implies missing process steps, but only with your approval.

### 24.1 Meta-workflow layer

Introduce a `ProcessImprovementProposal` entity.

Fields:
- trigger_event
- observed_problem_pattern
- proposed_new_step
- expected_benefit
- implementation_scope
- approval_status

### 24.2 Example

If repeated feedback says “equations flash by too quickly”, the system may propose:

> Add a readability timing pass before final render, enforcing minimum hold time for new equations.

This proposal should appear in the dashboard as a process-level change request.

Only after your approval should it be inserted into the active workflow template.

---

## 25. Testing strategy

### 25.1 Unit tests

- source parsing
- claim linking
- topic ranking
- layout metrics
- approval state transitions
- upload prechecks

### 25.2 Integration tests

- end-to-end from idea to waiting approval
- script to render bundle
- render to final preview
- upload dry-run

### 25.3 Visual regression tests

- screenshot comparison for standard components
- subtitle-safe area checks
- overlap metric stability

### 25.4 Synthetic acceptance suites

Create benchmark topics such as:

- singular value decomposition intuition
- chain rule in backprop
- epsilon-delta limit intuition
- why eigenvectors matter in PCA

Use them as repeatable test cases.

---

## 26. Safety and editorial policy

### 26.1 Math safety

- no unsupported theorem statements
- no fake proofs
- no historical claims without source
- clearly label intuition vs theorem vs analogy

### 26.2 Platform safety

- respect upload rate limits
- respect music licensing
- keep metadata truthful
- store audit trail for uploads

### 26.3 Operational safety

- sandbox code generation
- restrict filesystem scope for generated code execution
- timeout long renders
- memory limits on workers
- no shell execution from unreviewed prompts without sanitisation

---

## 27. Minimum viable build order

Build this in phases.

### Phase 1 — Skeleton
- FastAPI backend
- PostgreSQL schema
- React dashboard skeleton
- Celery + Redis
- video state machine
- manual topic entry

### Phase 2 — Research grounding
- source fetchers
- claim/source schema
- topic cards with references
- idea approval UI

### Phase 3 — Script system
- script generator
- reviewer passes
- script approval UI

### Phase 4 — Manim generation
- scene manifest
- reusable Manim component library
- render service
- preview assets

### Phase 5 — QA repair loop
- geometry overlap checker
- screenshot review pass
- deterministic repair system

### Phase 6 — Narration + audio
- local TTS
- subtitle alignment
- BGM mixer

### Phase 7 — Final composition + review
- final MP4 generation
- preview player
- final approval UI

### Phase 8 — Platform publishing
- YouTube publisher
- Instagram publisher
- upload approval UI

### Phase 9 — Full autonomy
- always-on topic scheduler
- concurrency controls
- dashboard metrics
- process-improvement proposals

---

## 28. Suggested prompt architecture

Separate prompts by job instead of one universal prompt.

### Prompt families
- topic discovery
- research extraction
- claim normalisation
- short-form hook generation
- script writing
- script critique
- scene manifest generation
- Manim code generation
- Manim repair prompt
- title/description generation
- revision brief generation

Store prompts in versioned files and attach prompt version to outputs.

---

## 29. Key implementation rules for Claude Code

When using this document as Claude Code instruction, enforce these rules:

1. Prefer adding typed schemas before adding new workflow logic.
2. Never let a worker skip an approval gate.
3. Never let script generation proceed if core claims are unsupported.
4. Never let final render proceed without Manim QA pass results.
5. Always preserve prior versions; do not overwrite approved artifacts.
6. Every stage must be resumable and idempotent.
7. Treat platform upload as optional capability, not guaranteed entitlement.
8. Keep generated Manim code deterministic and inspectable.
9. Put layout logic in reusable helpers, not scattered coordinates.
10. Log every automated repair and every rejection reason.

---

## 30. Recommended first repository milestone

Your first serious milestone should be:

> “A locally running dashboard where the system autonomously proposes 5 referenced video ideas, lets me approve one, generates a referenced 60-second script, lets me approve it, produces a Manim preview with overlap QA report, and shows the result in a browser.”

Do **not** start with uploads.
Do **not** start with perfect TTS.
Do **not** start with full autonomy.

First prove the editorial loop and the Manim QA loop.

---

## 31. Pseudocode for the core supervisor

```python
while True:
    refresh_system_health()
    ensure_topic_buffer(min_ideas=5)
    ensure_script_buffer(min_scripts=3)
    ensure_final_buffer(min_finals=2)

    for video in runnable_videos():
        if video.waiting_for_approval:
            continue
        enqueue_next_stage(video)

    recover_stalled_jobs()
    collect_metrics()
    sleep(POLL_INTERVAL)
```

---

## 32. Example end-to-end run

### Video example
Topic: “Why singular values measure stretching”
Type: theory
Audience: early undergrad / AI learners

Flow:

1. Topic engine proposes the idea with textbook + linear algebra references.
2. You approve idea.
3. Script worker generates a 145-word script and 5-scene plan.
4. Reviewer pass shortens jargon and flags one unsupported claim.
5. Research worker adds an additional source.
6. You approve script.
7. Manim worker generates scenes.
8. QA finds caption overlap in scene 3 and dense labels in scene 4.
9. Repair pass increases spacing and splits one scene.
10. TTS generates narration.
11. FFmpeg composes preview.
12. You approve final.
13. Upload screen shows YouTube ready, Instagram not connected.
14. You approve YouTube only.
15. System uploads privately and records video id.

---

## 33. Final recommendation

Build this as a **workflow engine with editorial control**, not as a single monolithic “AI script-to-video” app.

The crucial technical differentiators are:

- source-grounded claim architecture
- deterministic Manim layout helpers
- automated overlap/crowding QA with repair loop
- approval-first state machine
- local dashboard with resumable jobs
- resource-aware parallel workers

If you get those right, the rest is iteration.

---

## 34. Reference notes for implementation

These are the main external facts this plan is built around:

1. Manim provides compositional layout tools and spacing controls such as arranging grouped objects and configurable `buff`, which supports building deterministic anti-overlap helpers.
2. YouTube Data API supports uploads, but new unverified API projects are restricted to private uploads until audit.
3. Instagram Graph API supports publishing single media posts including reels for eligible business/creator setups, so account readiness must be checked.
4. Crossref exposes open metadata retrieval APIs, making it suitable for bibliographic grounding.
5. Semantic Scholar provides developer APIs for academic discovery.
6. Ollama offers a local API for serving models.
7. faster-whisper is a local open-source Whisper reimplementation suitable for transcript QA.
8. Playwright supports screenshot automation, useful for dashboard tests and visual checks.

