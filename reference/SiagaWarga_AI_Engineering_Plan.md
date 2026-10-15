# SiagaWarga --- AI Engineering Implementation Plan

**Scope:** model selection, integration, evaluation, inference API, and
demo-ready deployment\
**Role:** AI Engineer\
**Project principle:** *Use existing pretrained models and services
wherever practical. Do not train a model from scratch for the MVP.*

------------------------------------------------------------------------

## 1. Mission and Definition of Done

The AI Engineer's responsibility is to turn existing AI capabilities
into a reliable feature that the SiagaWarga demo can use. The goal is
not to invent a new model. The goal is to select suitable pretrained
models, connect them to the application, measure their limitations, and
deploy an inference service that works consistently during the demo.

### MVP outcome

A user submits a report containing a photo, description, and location.
The AI service returns structured suggestions:

-   predicted incident category
-   model confidence or similarity score, clearly labeled
-   optional short description of visible evidence
-   whether the result needs human review
-   model/version metadata for debugging

The backend combines this output with deterministic business rules to
calculate priority. **The model must not independently decide emergency
response priority.**

### Definition of done

-   [ ] Inference works on the agreed incident categories.
-   [ ] The API accepts an image and/or text according to a documented
    schema.
-   [ ] The API returns valid, predictable JSON, including error cases.
-   [ ] Inference latency and memory use are measured on the intended
    deployment environment.
-   [ ] A small labeled evaluation set has been tested and results
    documented.
-   [ ] Low-confidence and ambiguous predictions trigger review instead
    of being treated as facts.
-   [ ] The app can call the service from the demo environment.
-   [ ] Model name, version, license, limitations, and setup steps are
    documented.
-   [ ] There is a fallback path if the model or external API is
    unavailable.

------------------------------------------------------------------------

## 2. Product Scope: What AI Does and Does Not Do

### In scope

1.  **Image-based incident classification:** suggest whether an image
    depicts a pothole, cracked road, flooded road, garbage, fallen tree,
    or broken street light.
2.  **Text-based classification:** infer a likely category from the
    citizen's description.
3.  **Optional text-image agreement check:** identify cases where the
    photo and description suggest different categories.
4.  **Structured output:** return category, scores, and review flags for
    the backend.
5.  **Human review support:** expose uncertain cases to the officer
    rather than silently making a definitive claim.

### Out of scope for the first demo

-   Training a new foundation model or custom deep-learning model from
    scratch.
-   Claiming city-wide or real-world accuracy based on a few examples.
-   Automatically dispatching emergency services.
-   Automatically rejecting reports based on AI.
-   Inferring exact geographic location from an image.
-   Treating model confidence as severity, urgency, or factual
    certainty.
-   Building a complex multi-agent system.
-   Adding several models before the first baseline has been evaluated.

------------------------------------------------------------------------

## 3. Agreed Incident Taxonomy

Start with a small, consistent label set. Use the same canonical
category IDs in the model adapter, API, database, and frontend.

  -----------------------------------------------------------------------
  Canonical ID            Display label           Example evidence
  ----------------------- ----------------------- -----------------------
  `pothole`               Jalan berlubang         One or more holes in
                                                  road surface

  `cracked_road`          Jalan retak/rusak       Cracks or broken road
                                                  surface without a clear
                                                  pothole

  `flooded_road`          Jalan tergenang         Water covering part of
                                                  the road

  `garbage`               Sampah menumpuk         Garbage or waste on a
                                                  street/public area

  `fallen_tree`           Pohon tumbang           Fallen tree or large
                                                  branch obstructing an
                                                  area

  `broken_street_light`   Lampu jalan rusak       Street-light fixture
                                                  visibly damaged; a
                                                  photo may not prove
                                                  that a lamp is
                                                  electrically off

  `other_or_unclear`      Lainnya/belum jelas     None of the supported
                                                  categories can be
                                                  confidently selected
  -----------------------------------------------------------------------

**Important:** These categories are not all equally detectable from a
single photo. A broken light that is merely switched off may look normal
in daylight. Use text evidence or manual review for such cases.

Do not change labels casually after collecting evaluation results. If
the taxonomy changes, record the change and rerun evaluation.

------------------------------------------------------------------------

## 4. Model Strategy: Select Before You Build

### Decision order

1.  Check whether a suitable pretrained model can classify the required
    categories.
2.  Run it locally on representative images.
3.  Compare it against one alternative only if the baseline has a clear
    weakness.
4.  Choose based on quality, latency, deployment feasibility, license,
    and cost.
5.  Wrap the chosen model behind a stable API so it can be replaced
    later without changing the frontend.

### Candidate approaches

  -------------------------------------------------------------------------------
  Approach          Strengths            Risks / trade-offs     Recommended use
  ----------------- -------------------- ---------------------- -----------------
  Zero-shot         Can compare an image Similarity scores are  **First image
  image-text model  with category        not calibrated         baseline** when
  (for example, a   descriptions without probabilities; may     categories are
  CLIP-family       project-specific     confuse visually       broad and the
  model)            training; easy to    similar categories     demo has a
                    prototype                                   limited dataset

  Pretrained image  Usually faster and   Labels may not match;  Test if a
  classifier        more direct if its   domain and licensing   credible model
  trained on        label set matches    may be unsuitable      already covers
  relevant          the project                                 the categories
  road-damage                                                   
  categories                                                    

  Hosted vision API Fast integration,    Network dependency,    Candidate if
                    little               usage cost, privacy    internet
                    infrastructure,      considerations,        availability and
                    often robust general provider-specific      budget are
                    visual understanding output                 acceptable

  Pretrained text   Simple way to        Indonesian phrasing,   **First text
  classifier /      classify report      slang, spelling        baseline**
  zero-shot text    descriptions         errors, and            
  classification                         overlapping labels can 
                                         reduce quality         

  General-purpose   Can normalize messy  Can hallucinate, cost  Optional text
  LLM with          descriptions and     more, depend on        fallback; never
  structured output produce a            network, and require   accept its output
                    schema-constrained   careful                without schema
                    response             prompting/validation   validation
  -------------------------------------------------------------------------------

These are candidate approaches, not a claim that a particular model has
already passed evaluation. Verify each model's current model card,
supported language, license, inference requirements, and availability
before adoption.

### Model selection scorecard

Score each candidate from 1--5. Use measured evidence where possible.

  ---------------------------------------------------------------------------
  Criterion                                   Weight What to check
  --------------------- ---------------------------- ------------------------
  Category fit /                                 30% Correct predictions on a
  evaluation results                                 small labeled test set

  Demo reliability                               20% Repeatable outputs,
                                                     manageable errors

  Deployment fit                                 20% CPU/GPU/RAM, startup
                                                     time, hosting
                                                     compatibility

  Latency                                        10% Median and slow-case
                                                     response time

  License and data                               10% Commercial/competition
  handling                                           use, image retention,
                                                     privacy

  Cost and operational                           10% Free tier limits,
  simplicity                                         per-request costs, setup
                                                     burden
  ---------------------------------------------------------------------------

Do not select a model solely because its model-card benchmark is high.
The relevant question is whether it works on SiagaWarga's images and
Indonesian reports.

------------------------------------------------------------------------

## 5. Current Baseline: Image Classification

The current experiment has produced the following output for one road
image:

-   `a pothole in a road`: 81.42%
-   `a cracked road`: 18.06%
-   `a flooded road`: 0.49%
-   other candidate labels: near zero

This is a useful **smoke test**: the code loaded a model and produced
ranked candidate labels for an image that visibly contains potholes. It
does **not** establish overall accuracy.

If the model is CLIP or another zero-shot image-text model, the values
are generally relative scores over the candidate descriptions (often
normalized by softmax). They must not be presented as an 81.42%
probability that the prediction is true unless the score has been
separately calibrated and validated.

### Immediate tasks

-   [ ] Record the exact model ID, library, model revision, and
    candidate text labels used by `test.py`.
-   [ ] Record Python and dependency versions.
-   [ ] Run inference on 20--50 labeled images across the agreed
    categories.
-   [ ] Include difficult examples: rain, shadows, low light, distant
    objects, road repairs, water-filled potholes, and irrelevant images.
-   [ ] Inspect false positives and false negatives, not only the top
    score.
-   [ ] Measure cold-start time, warm inference time, and peak memory.
-   [ ] Save a small CSV containing image ID, ground-truth category,
    predicted category, top score, second score, and correct/incorrect.

### Minimum evaluation metrics

-   **Top-1 accuracy:** fraction of examples where the highest-ranked
    category matches the label.
-   **Per-class precision and recall:** reveals categories that are
    over-predicted or missed.
-   **Confusion matrix:** reveals which categories the model confuses.
-   **Latency:** report median and 95th-percentile if enough requests
    are available.
-   **Review rate:** percentage of examples flagged as uncertain.

For a very small evaluation set, describe results as preliminary. Do not
imply statistical certainty.

------------------------------------------------------------------------

## 6. Text Classification Strategy

Text classification is a separate capability from image classification.
Do not assume an image model can classify Indonesian report
descriptions.

Example input:

> "Dari kemarin ada lubang besar di depan sekolah, kalau hujan penuh air
> dan motor hampir jatuh."

Desired normalized result:

-   category: `pothole`
-   language: `id`
-   review_required: false or true depending on the evidence and score
-   evidence: concise phrase based only on the report
-   scores: supplied by the chosen model, if meaningful

### Recommended workflow

1.  Collect 30--100 representative example descriptions for initial
    testing. They may be manually authored for smoke testing, but do not
    describe them as a representative real-world dataset.
2.  Include spelling variation, colloquial Indonesian, short reports,
    ambiguous descriptions, and reports that mention multiple problems.
3.  Test a pretrained Indonesian-capable classifier or a multilingual
    zero-shot text classifier.
4.  Compare results on the same labeled examples.
5.  Use a general-purpose LLM only if it improves the test results
    enough to justify latency, cost, and network dependence.
6.  Validate the returned category against the canonical taxonomy.
7.  If text and image disagree, return a mismatch flag and ask for human
    verification.

### Example test cases

  Text                                               Expected category
  -------------------------------------------------- ------------------------------------
  "Banyak lubang besar di tengah jalan."             `pothole`
  "Aspal retak memanjang dekat persimpangan."        `cracked_road`
  "Air hujan menutup sebagian badan jalan."          `flooded_road`
  "Sampah rumah tangga menumpuk di pinggir jalan."   `garbage`
  "Pohon besar roboh dan menutup akses."             `fallen_tree`
  "Tiang lampu jalan rusak setelah tertabrak."       `broken_street_light`
  "Mohon segera diperbaiki."                         `other_or_unclear` or human review

These are test examples, not training data or proof of model
performance.

------------------------------------------------------------------------

## 7. Image + Text Fusion

Do not start by building a complex multimodal architecture. Begin with
two independent predictions and a simple consistency rule.

### Suggested logic

1.  If only a photo is supplied, run image classification.
2.  If only text is supplied, run text classification.
3.  If both are supplied, run both.
4.  If both agree and the scores are sufficiently strong, return the
    agreed category.
5.  If they disagree, or either output is uncertain, set
    `review_required: true`.
6.  Never average incomparable scores from different models as if they
    were the same probability scale.

A simple policy is preferable to an opaque formula for the first demo.

------------------------------------------------------------------------

## 8. API Contract

Keep the frontend independent of the model implementation. The backend
should call a stable AI endpoint.

### Endpoint

`POST /api/v1/classify-report`

For the MVP, multipart form data is convenient for an uploaded image
plus text fields. If the existing backend has a different standard,
follow it consistently.

### Conceptual response

``` json
{
  "category": "pothole",
  "display_label": "Jalan berlubang",
  "source": {
    "image": "pothole",
    "text": "pothole"
  },
  "score": 0.81,
  "score_type": "relative_candidate_score",
  "review_required": false,
  "model": {
    "id": "exact-model-id",
    "revision": "recorded-revision"
  },
  "warnings": []
}
```

This is an example schema only. Replace the model ID and score semantics
with actual values from the chosen model. If image and text models
return incomparable scores, return separate `image_score` and
`text_score` fields instead of one combined score.

### API requirements

-   Validate file type and file size.
-   Reject empty or unreadable files with a clear error.
-   Normalize orientation and image mode as required by the model
    processor.
-   Use a request timeout.
-   Return consistent JSON for errors.
-   Avoid logging raw images, credentials, or sensitive report text
    unnecessarily.
-   Do not expose model credentials to the frontend.
-   Include a health endpoint such as `GET /health`.
-   Add basic rate limiting if the endpoint is exposed publicly.
-   Document required environment variables in `.env.example`; never
    commit secrets.

### Example error response

``` json
{
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "Upload a supported image format."
  }
}
```

------------------------------------------------------------------------

## 9. Priority Engine Is Not the AI Model

The AI service proposes a category and may provide visual/textual
evidence. The application backend calculates operational priority.

Keep these concepts separate:

-   **Category:** what type of problem is reported.
-   **Severity:** how harmful the issue could be, based on defined
    criteria and verified information.
-   **Confidence / score:** how strongly the model favors its
    prediction; depends on the model's scoring method.
-   **Priority:** the operational order for review or response, based on
    approved rules and context.

### MVP policy

-   AI classification does not automatically set an incident to
    "critical."
-   A low-confidence result triggers review; it must not silently lower
    priority.
-   High-risk indicators can trigger an urgent review queue, but the
    rule should be explicit and auditable.
-   Location impact, number of affected people, duplicate reports, and
    waiting time should be sourced from actual application data or
    clearly marked estimates.
-   Do not use the number of duplicate reports as the sole measure of
    danger.
-   The score formula and thresholds must be documented and configurable
    by the project team.
-   Use a synthetic/demo dataset for the presentation if no verified
    real data is available, and label it as demo data.

For the first demo, it is acceptable to implement a transparent
rule-based score. Avoid claiming that the score is an empirically
validated prediction of harm.

------------------------------------------------------------------------

## 10. Evaluation Dataset and Testing Protocol

### Build a small, honest evaluation set

A practical first pass is 20--50 images, with examples spread across
categories. If some categories have very few images, state that clearly
and do not compare their metrics as if they were equally reliable.

For each sample, record:

-   sample ID
-   image path or safe reference
-   ground-truth category
-   prediction
-   score and score type
-   correct / incorrect
-   error notes
-   model ID and revision

For text, maintain a separate labeled set. Keep the test examples fixed
when comparing model candidates so the comparison is fair.

### Data sources

Prefer images that have clear usage rights and a suitable license.
Record source and license information. Do not scrape arbitrary images
and assume they are safe to reuse. Do not include private addresses,
faces, license plates, or identifiable bystanders in the public demo
unless there is a valid reason and appropriate handling.

### Acceptance gates for the demo

These are **project targets**, not claims about current performance:

-   The service starts reliably from a clean setup.
-   The API returns the expected schema for valid input and clear errors
    for invalid input.
-   Every supported category has at least some test coverage, or is
    explicitly marked as not yet validated.
-   Results are documented with a confusion matrix or per-class error
    table.
-   Uncertain cases are surfaced for review.
-   Latency is measured on the actual demo host.
-   A fallback manual category selection is available if inference
    fails.

Do not promise a specific accuracy target until the team agrees on it
and the dataset is adequate.

------------------------------------------------------------------------

## 11. Deployment Plan

### Recommended MVP architecture

**Frontend → Existing application backend → AI inference service →
structured prediction → backend priority rules → database/dashboard**

Do not let the browser call a private model provider directly. Keep API
keys and model logic on the server.

### Deployment options

  -----------------------------------------------------------------------
  Option                  Advantages              Considerations
  ----------------------- ----------------------- -----------------------
  Same backend process    Simple for a tiny demo  Model dependencies can
                                                  make the app large;
                                                  slow model loading may
                                                  affect other endpoints

  Separate Python         Clear separation, easy  Requires an additional
  inference API           to test and replace     service and health
                          models                  monitoring

  Hosted inference API    Less model              Internet, price limits,
                          infrastructure to       privacy, provider
                          manage                  availability, and
                                                  latency
  -----------------------------------------------------------------------

**Default recommendation:** if the current experiment uses Python and
the product backend uses a different stack, wrap the selected model in a
small FastAPI service. Keep it separate only if deployment complexity
remains manageable. For the fastest demo, a hosted API may be preferable
if data/privacy requirements and network availability permit it.

### Deployment checklist

-   [ ] Pin dependencies and model revision where supported.
-   [ ] Load the model once at startup rather than once per request.
-   [ ] Use CPU-friendly settings unless a GPU is actually available.
-   [ ] Measure memory and cold-start behavior on the target host.
-   [ ] Add `/health` and a startup readiness check.
-   [ ] Set request timeout and upload-size limit.
-   [ ] Test the service from the deployed frontend, not only from a
    local script.
-   [ ] Configure secrets using deployment environment variables.
-   [ ] Test a request after redeploy/restart.
-   [ ] Prepare a manual fallback if the model host is unavailable.
-   [ ] Confirm model license and hosting terms before public
    deployment.

Do not assume a model that runs on a developer laptop will fit the free
tier of a hosting platform. Confirm RAM, disk, CPU/GPU, cold-start
limits, and outbound network restrictions.

------------------------------------------------------------------------

## 12. Prompt Templates for AI Engineering Work

Use these prompts in separate sessions or tasks. Always attach the
current code, model ID, error trace, and constraints when relevant. Ask
for minimal changes and executable tests rather than broad rewrites.

### Prompt A --- Model selection research

> You are the AI Engineer for SiagaWarga, an Indonesian
> citizen-reporting prototype. We need deployable pretrained models, not
> training from scratch. Required labels: pothole, cracked road, flooded
> road, garbage, fallen tree, broken street light, and other/unclear.
> Compare candidate existing models for image classification and
> Indonesian text classification. For each candidate, provide the exact
> model ID, model-card link, license, supported languages/categories,
> inference library, approximate CPU/RAM needs if documented, known
> limitations, and a minimal local inference test. Distinguish verified
> facts from assumptions. Do not claim suitability until evaluated on
> our test samples. Prefer a simple baseline and explain the fastest
> route to a working demo.

### Prompt B --- Inspect the existing image experiment

> Review the attached `test.py` and its console output. Identify the
> exact model architecture and scoring method from the code, explain
> what the displayed scores mean, and determine whether they are
> probabilities or relative similarity scores. Do not guess missing
> details. Recommend the smallest changes needed to run a reproducible
> evaluation on labeled examples. Keep the current working inference
> path intact unless a concrete issue requires a change.

### Prompt C --- Build an evaluation script

> Create a small evaluation script for the existing SiagaWarga image
> classifier. Input: a CSV containing image path and ground-truth
> canonical category. Output: predictions, score values,
> correct/incorrect flags, per-class precision/recall, overall top-1
> accuracy, confusion matrix, and a CSV of errors. Preserve the exact
> model and label descriptions used by the current inference code.
> Include dependency/setup instructions and handle missing or unreadable
> images. Do not train or fine-tune a model.

### Prompt D --- Compare candidate models fairly

> Compare the current baseline with one alternative on the same fixed
> labeled evaluation set. Do not train either model. Report top-1
> accuracy, per-class precision/recall, confusion matrix, latency,
> memory if measurable, model size, license, and setup complexity.
> Explain where each model fails. Recommend one for the demo using
> measured results and deployment constraints, not popularity or
> benchmark scores alone.

### Prompt E --- Implement a FastAPI inference wrapper

> Wrap the selected existing pretrained model in a small FastAPI service
> for SiagaWarga. Load the model once at startup. Implement
> `GET /health` and `POST /api/v1/classify-report`. Validate image
> uploads, accept an optional Indonesian description, and return a
> stable JSON schema using the canonical categories. Include model
> ID/revision and clearly document score semantics. Handle invalid
> files, missing inputs, model errors, and timeouts. Do not train a
> model, expose secrets, or invent accuracy claims. Provide complete
> runnable files, pinned dependencies, `.env.example` only if needed,
> and curl tests.

### Prompt F --- Add uncertainty handling

> Add conservative uncertainty handling to the current classifier. First
> inspect the model's actual score semantics. Do not treat a zero-shot
> similarity score as calibrated probability. Use a configurable
> threshold and, if useful, a top-1/top-2 score gap only as an
> empirically tested heuristic. Return `review_required: true` for
> ambiguous or unsupported cases. Explain how to choose thresholds from
> the labeled validation set and add tests for uncertain outputs. Do not
> let low confidence automatically reduce incident priority.

### Prompt G --- Integrate with the product backend

> Integrate the deployed SiagaWarga AI endpoint with the existing
> backend. Inspect the current repository and follow its conventions.
> The frontend must not call private model-provider APIs directly.
> Validate the response schema, persist the prediction and model
> metadata, and retain manual category correction. If the AI service
> fails, allow a report to be submitted with a manual category and mark
> AI classification as unavailable. Make the smallest cohesive changes
> and provide tests for success, low confidence, and service failure.

### Prompt H --- Diagnose deployment failure

> Diagnose the deployment failure using the attached logs, environment,
> and repository files. Find the root cause before proposing changes.
> Check dependency compatibility, model download/cache, memory, startup
> timeout, environment variables, request size, network access, and
> health checks as relevant. Do not replace the model or rewrite the
> service without evidence. Provide the smallest fix and exact commands
> to verify it.

### Prompt I --- Prepare a demo-safe fallback

> Design a fallback for SiagaWarga if model inference is slow or
> unavailable during the presentation. Preserve the real model
> integration, but allow manual category selection and clearly mark AI
> status as unavailable. Do not fake live model results or present
> prerecorded predictions as real-time inference. Provide a repeatable
> demo script and tests for both successful inference and failure mode.

### Prompt J --- Technical defense for judges

> Prepare a concise technical explanation of the SiagaWarga AI pipeline
> for software-development competition judges. Explain the selected
> pretrained model, why it was chosen over alternatives, evaluation
> method and actual results, score semantics, uncertainty handling, API
> architecture, deployment, limitations, and why priority is calculated
> separately from model confidence. Use only evidence in the supplied
> repository and evaluation report. Clearly identify anything not yet
> measured.

------------------------------------------------------------------------

## 13. Suggested Repository Structure

Adapt to the existing repository; do not reorganize everything just for
aesthetics.

``` text
SiagaWarga/
├── ai-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── classifier.py
│   │   ├── schemas.py
│   │   └── settings.py
│   ├── tests/
│   ├── evaluation/
│   │   ├── samples.csv
│   │   └── evaluate.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── docs/
│   └── ai-model-evaluation.md
└── ...
```

Keep model weights out of Git unless they are small and the repository
policy permits them. Document model download/cache behavior.

------------------------------------------------------------------------

## 14. Two-Week Execution Plan

This is a suggested plan for the AI workstream, assuming the application
team is building the rest of the product in parallel.

  -----------------------------------------------------------------------
  Day                     Deliverable             Priority
  ----------------------- ----------------------- -----------------------
  1                       Inspect current         P0
                          `test.py`, identify     
                          exact model, lock       
                          taxonomy                

  2                       Run smoke tests and     P0
                          collect a small labeled 
                          evaluation set          

  3                       Evaluate image baseline P0
                          and document failure    
                          cases                   

  4                       Test one alternative    P0
                          only if baseline is     
                          inadequate              

  5                       Select image model and  P0
                          stabilize inference     
                          code                    

  6                       Build API schema,       P0
                          health endpoint, error  
                          handling                

  7                       Integrate image         P0
                          inference with backend  

  8                       Add text classification P1
                          baseline if it          
                          materially improves the 
                          demo                    

  9                       Add conservative review P0
                          flags and manual        
                          override                

  10                      Deploy to target host   P0
                          and test end-to-end     

  11                      Fix measured            P0
                          latency/reliability     
                          issues                  

  12                      Run evaluation          P0
                          regression and record   
                          actual results          

  13                      Prepare demo fallback   P0
                          and judge-facing        
                          explanation             

  14                      Freeze                  P0
                          dependencies/model      
                          revision; rehearse      
                          clean startup           
  -----------------------------------------------------------------------

If time becomes tight, drop optional text-model integration before
dropping API reliability, evaluation, or the manual fallback.

------------------------------------------------------------------------

## 15. Priority Labels

### P0 --- Required for a credible demo

-   Identify and document the current model.
-   Fix canonical categories.
-   Evaluate on labeled examples.
-   Keep score semantics honest.
-   Implement stable inference API.
-   Add uncertainty and manual override.
-   Deploy and test end-to-end.
-   Provide a fallback.
-   Document real limitations and measured results.

### P1 --- Add only after P0 is stable

-   Text classification.
-   Image-text agreement checks.
-   Better threshold calibration.
-   Duplicate incident suggestions.
-   Performance optimizations based on measurements.

### P2 --- Not for the first demo

-   Custom model training or fine-tuning.
-   Complex multimodal fusion.
-   Real-time emergency dispatch.
-   Large-scale active learning.
-   Model ensembles without proven benefit.
-   Automated severity decisions from images alone.

------------------------------------------------------------------------

## 16. Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Model misclassifies local road      Evaluate Indonesian/local examples;
  conditions                          keep manual correction

  Score is mistaken for probability   Document score type in API and UI

  Categories overlap visually         Use text evidence, review flags,
                                      and confusion analysis

  Hosted model unavailable during     Health checks, fallback, and
  demo                                rehearsal

  Model too large for hosting         Measure RAM/startup on target host;
                                      choose a smaller model or hosted
                                      API

  LLM returns invalid labels or       Constrain schema, validate
  invented facts                      category, and use only
                                      evidence-supported fields

  Public photos expose personal data  Minimize retention, restrict logs,
                                      and avoid unnecessary identifiable
                                      imagery

  Priority logic overstates danger    Keep priority rules separate,
                                      transparent, and human-reviewable

  License unsuitable                  Verify model card/license and
                                      provider terms before deployment
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 17. Required Technical Notes

Maintain `docs/ai-model-evaluation.md` with:

1.  Problem statement and canonical labels.
2.  Exact model ID and revision.
3.  Model card and license.
4.  Library and dependency versions.
5.  Hardware/hosting environment.
6.  Evaluation-set source and label method.
7.  Metrics and confusion matrix.
8.  Latency and memory measurements.
9.  Known failure cases.
10. API schema and example request/response.
11. Deployment instructions and fallback behavior.
12. Date of last evaluation and the person who ran it.

This is valuable for debugging, team handoff, and answering judges'
questions.

------------------------------------------------------------------------

## 18. Immediate Next Session

Do these in order:

1.  Open the current `test.py`.
2.  Identify the exact model ID, candidate labels, preprocessing, and
    score calculation.
3.  Run the existing script successfully on the current image.
4.  Add a CSV-driven evaluation path without changing the model.
5.  Gather a small, labeled test set.
6.  Measure baseline results and identify the largest errors.
7.  Only then decide whether to keep the model or compare one
    alternative.
8.  After selecting the model, expose it through the inference API and
    deploy it.

### Information to bring into the next AI engineering session

-   Current `test.py`
-   `requirements.txt` or package list
-   Exact model ID
-   One or more representative sample images
-   Labelled CSV, when available
-   Target backend/frontend stack
-   Intended deployment host and its free-tier resource limits

**Final principle:** SiagaWarga does not need the most impressive model
on paper. It needs the simplest model that works adequately on the
intended reports, can be evaluated honestly, can be called reliably by
the application, and can survive the live demo.
