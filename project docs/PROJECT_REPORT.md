# AI-Based Fake News Detection Using Large Language Models

**Department of MCA, RVCE &nbsp;&nbsp;&nbsp;&nbsp; 2025-26**

---

# CHAPTER 1

# INTRODUCTION

## 1.1 Project Overview

The rapid proliferation of digital media platforms has fundamentally altered the information landscape. While these platforms have democratised access to news and enabled real-time global communication, they have simultaneously created fertile ground for the mass production and distribution of misinformation, disinformation, and fabricated content commonly referred to as "fake news" [1]. The problem has grown from an academic curiosity into a societal emergency that affects electoral integrity, public health decision-making, and communal harmony, particularly in densely connected societies such as India where messaging applications like WhatsApp serve as primary news sources for hundreds of millions of people [2].

This project presents an AI-powered fake news detection platform that classifies user-submitted news articles as **REAL** or **FAKE** using a production-quality multi-tier Large Language Model (LLM) pipeline. Unlike academic prototypes that demonstrate classification accuracy on benchmark datasets without addressing operational realities, this system is engineered for deployment: it remains fully functional even when cloud AI services are unavailable, provides human-readable explanations for every verdict, stores user history for longitudinal analysis, and exposes an administrative interface for platform governance.

The system is architected around three complementary AI tiers. The first tier uses the Groq cloud API to invoke Llama 3.3 70B, a state-of-the-art 70-billion-parameter language model that achieves near-human accuracy on fact-verification tasks [3]. The second tier uses Ollama to run Microsoft's Phi-3 Mini model locally on the host machine, providing offline capability without sacrificing explainability [4]. The third tier is a deterministic heuristic engine containing over 60 domain-specific regex patterns derived from empirical studies of fake news linguistic features [5][6], which executes in under 200 milliseconds and requires no external service of any kind. Each tier's output is enriched by an external evidence layer that queries the Google Fact Check Tools API, searches 12 trusted news domains via RSS, and optionally integrates with NewsAPI.org for corroborating article retrieval.

Beyond the detection engine, the platform provides a complete web application experience. Users register accounts, submit news text through an intuitive detection interface, receive structured verdicts with explanations, and review their prediction history with search and filter capabilities. Sentiment analysis powered by TextBlob [7] and keyword extraction powered by NLTK [8] accompany every prediction, giving users linguistic context alongside the binary classification. An administrator panel provides platform governance through user management, activity monitoring, prediction timeline visualisations, and a full audit log of administrative actions.

The project is built on a Flask 3.0 Python backend with SQLAlchemy ORM, JWT and session-based dual authentication, and a Jinja2 + Tailwind CSS frontend. The database schema supports both SQLite for development and MySQL for production deployment via PyMySQL.

## 1.2 Problem Statement

Fake news has become one of the most significant threats to modern democratic societies. A landmark study published in Science by Vosoughi et al. [2] analysed 126,000 news stories shared on Twitter between 2006 and 2017 and found that false news spread significantly farther, faster, deeper, and more broadly than true news in all categories of information. The authors found that false political news was retweeted three times more often than true political news, and that emotional novelty — not bots — was the primary driver of this propagation.

In India specifically, the consequences of fake news are documented and severe. The NCRB annual report [9] recorded thousands of cybercrime cases related to spreading misinformation, while WhatsApp forwards containing fabricated medical advice during the COVID-19 pandemic contributed to public health harm. Despite this, individuals attempting to verify news in real time face a fragmented and inadequate toolset. The core problems are:

**Data Scale Mismatch**: According to Lazer et al. [10], the volume of content produced on digital platforms overwhelms any manual fact-checking capacity. Professional fact-checking organisations such as AltNews, Boom Live, and AFP Fact Check in India collectively process a tiny fraction of the misinformation that circulates daily. Automated tools are not a luxury but a necessity.

**Absence of Explainability**: Most automated classifiers return a binary label without justification [11]. A system that says "FAKE" without explaining why is not actionable. A journalist, student, or policymaker needs to understand the reasoning behind a verdict to evaluate its credibility and decide on a course of action.

**Single-Model Brittleness**: Research systems typically demonstrate classification accuracy on test sets without addressing what happens when the AI model is unavailable, slow, or overloaded. A system that fails completely when its sole model times out is not production-ready.

**No External Evidence Grounding**: Pérez-Rosas et al. [12] showed that purely linguistic classifiers have an accuracy ceiling because well-crafted fake news can mimic legitimate writing styles. Systems that do not cross-reference predictions against verified fact databases or trusted news coverage miss the most powerful signal available: whether established organisations have already investigated and rated the claim.

**No User Context and History**: Existing tools treat each submission in isolation. A user who regularly checks news about a particular topic has no way to review their history, observe trends in what they encounter, or receive personalised insights.

**Inaccessibility to Non-Technical Users**: Existing NLP-based research tools require Python environments, command-line access, or API keys to operate. There is no freely available, web-based, account-enabled platform that brings LLM-powered fake news detection to a general audience without technical prerequisites.

This project is designed to address all six of these gaps within a single, coherent platform.

## 1.3 Objectives of the Project

The primary objectives of this project are:

1. To design and implement a three-tier LLM inference pipeline that routes news text sequentially through Groq Llama 3.3 70B, Ollama Phi-3 Mini, and a heuristic fallback, ensuring uninterrupted classification capability under all network and hardware conditions.

2. To build a heuristic pattern engine containing over 60 curated fake news indicator patterns and 6 credible-source indicator patterns, derived from empirical linguistics research [5][6][13], covering sports misinformation, political hoaxes, health conspiracy claims, financial scams, conspiracy tropes, and viral manipulation tactics specific to the Indian context.

3. To integrate an enrichment layer that cross-references predictions against the Google Fact Check Tools API, searches 12 established Indian and international news domains via Google News RSS using a parallel ThreadPoolExecutor architecture, and optionally queries NewsAPI.org for additional corroboration.

4. To implement sentiment analysis using TextBlob [7] and keyword extraction using NLTK [8] to provide users with linguistic context and supplementary signals alongside the binary classification verdict.

5. To implement an OCR text cleaning pipeline that strips news-logo watermarks, normalises character repetition artefacts, and removes OCR noise from text extracted from screenshot images before it is passed to the inference engine.

6. To create a full-stack web application with Flask blueprints, SQLAlchemy models, dual JWT and session-based authentication, bcrypt password hashing, paginated prediction history, user dashboard, and a real-time admin analytics panel.

7. To validate the complete system through a test suite of over 70 test cases spanning 10 subject categories, verifying that the heuristic engine achieves the expected verdict with confidence ≥ 80% across space science, politics, health, sports, finance, science, general knowledge, and regional Indian facts.

## 1.4 Scope and Significance

The scope of this project encompasses the following technical domains:

- Natural language processing and LLM-based zero-shot text classification [3][14]
- Rule-based heuristic pattern matching and multi-signal scoring [5][6]
- External API integration: Groq API, NewsAPI.org, Google Fact Check Tools API
- RSS feed parsing and parallel trusted-source cross-referencing
- Full-stack web development: Flask 3.0, Jinja2, Tailwind CSS
- Relational database design and ORM: SQLAlchemy, SQLite, MySQL
- JWT-based and session-based authentication with bcrypt password hashing
- Role-based access control and administrative panel development
- Sentiment analysis (TextBlob) and NLP preprocessing (NLTK)
- Gunicorn-based WSGI production deployment

The significance of the project extends beyond its academic context. A fully operational version of this system could serve as a freely accessible fact-checking resource for Indian citizens, a training aid for media literacy programmes in educational institutions, a moderation support tool for community administrators on messaging platforms, and a backend API for mobile applications targeting rural communities where WhatsApp-distributed fake news has the most harmful impact.

From an academic perspective, this project operationalises several advances from the NLP and misinformation research literature — including chain-of-thought LLM prompting [15], heuristic linguistic feature scoring [6], trusted-source cross-referencing [16], and fact-check API integration [17] — in a single production-quality system with fault tolerance, user management, and explainability, demonstrating how academic findings can be translated into functional software.

---

# CHAPTER 2

# LITERATURE REVIEW

## 2.1 Fake News: Definition, Taxonomy, and Scale

The term "fake news" has been used inconsistently across popular media and academic literature. Tandoc et al. [18] analysed 34 academic studies published between 2003 and 2017 and proposed a taxonomy distinguishing satire, parody, fabrication, manipulation, advertising, and propaganda as distinct categories of false or misleading content. Their framework highlights that the term encompasses a spectrum from harmless humour to deliberate political manipulation, and that effective detection systems must account for this diversity. This project targets fabricated factual claims — the category that most directly enables public harm — while noting that the heuristic engine's patterns also flag several propaganda and manipulation indicators.

Wardle and Derakhshan [19] introduced the broader concept of "information disorder", classifying content along two axes: the intent to deceive and the potential for harm. They distinguish between misinformation (false content shared without deceptive intent), disinformation (false content shared with intent to cause harm), and malinformation (true content shared with intent to cause harm). While this project focuses primarily on detecting disinformation as it is the most tractable automated detection target, the enrichment layer's ability to retrieve fact-check ratings covers all three categories to varying degrees.

Allcott and Gentzkow [20] studied the role of fake news in the 2016 United States presidential election and found that the average American adult was exposed to approximately one or more fake news stories in the weeks before the election. Their study established the concept of recall-weighted exposure, showing that even a small number of convincing false articles can shift public opinion when consumed by large audiences. While the Indian context differs significantly, the mechanisms they describe — emotional resonance, partisan alignment, and source ambiguity — are directly reflected in the pattern categories implemented in the heuristic engine.

## 2.2 Automated Fake News Detection: Methods and Benchmarks

Shu et al. [1] provided the first comprehensive survey of automated fake news detection, classifying approaches into four broad categories: knowledge-based methods that verify claims against structured fact databases, style-based methods that analyse linguistic features of the article text, propagation-based methods that model the network patterns of how content spreads, and source-based methods that evaluate the credibility of the publishing outlet. The authors noted that no single method is sufficient and that hybrid approaches consistently outperform single-signal classifiers — a finding that directly motivated the multi-signal architecture of this project.

Wang [21] introduced the LIAR dataset, containing 12,836 short statements from PolitiFact.com with six-level truthfulness ratings. This dataset has become the de facto benchmark for fake news detection research. Zhou et al. [22] benchmarked multiple machine learning approaches on LIAR and found that models combining linguistic features with speaker credibility metadata achieve the highest macro-F1 scores. Their hybrid approach, which inspired the combination of LLM inference with trusted-source cross-referencing in this project, outperformed text-only classifiers by up to 12 percentage points.

Rashkin et al. [23] analysed the linguistic properties of fake news at scale using the LIAR and BS Detector datasets and found that fake news exhibits significantly higher rates of hedging language, stronger emotional polarity, and more frequent use of first and second person pronouns than legitimate news. Their findings are encoded as scoring factors in the heuristic analysis engine, particularly the emotional amplifier scoring that adds to the fake score when three or more high-arousal emotional words are detected.

Oshikawa et al. [24] provided a comprehensive survey of NLP approaches to fake news detection and identified three primary challenges: the domain shift problem (models trained on political fake news perform poorly on health misinformation), the adversarial adaptation problem (fake news producers adapt writing styles in response to detection systems), and the annotation bias problem (human annotators disagree on borderline cases). These challenges motivated the design decision to use a zero-shot LLM approach as the primary tier, as LLMs trained on internet-scale corpora exhibit far less domain-specific degradation than supervised classifiers.

Conroy et al. [25] surveyed early automatic deception detection approaches and proposed a hybrid framework combining knowledge networks with linguistic analysis. Their work established the foundational principle that cross-referencing claims against verified knowledge sources provides signal that pure linguistic analysis cannot capture — the same principle underlying the fact-check API and trusted-source search components of this project.

## 2.3 Deep Learning and Transformer-Based Detection

Devlin et al. [26] introduced BERT (Bidirectional Encoder Representations from Transformers), which revolutionised NLP by enabling contextual word representations. BERT fine-tuned on fake news datasets such as LIAR achieves substantially higher accuracy than traditional feature-based classifiers. Goldani et al. [27] specifically applied BERT to fake news detection and demonstrated that fine-tuned transformer models outperform CNN-LSTM hybrids by 4–8 percentage points on multiple benchmarks. While this project does not fine-tune BERT directly, the Groq-hosted Llama 3.3 70B model's attention mechanisms build on the same bidirectional contextualisation principles.

Liu et al. [28] introduced RoBERTa, a robustly optimised BERT approach that uses longer training, larger batches, and dynamic masking. Singhal et al. [29] applied RoBERTa to fake news detection and found it particularly effective at identifying domain-specific terminology mismatches, such as the scientific consensus violations that underpin health misinformation. The category detection function in the heuristic engine draws on similar domain-specific keyword matching to identify the subject domain before applying category-appropriate pattern weights.

Ruchansky et al. [30] proposed CSI (Capture, Score, Integrate), a hybrid deep model that combines article text features, user behaviour patterns, and source profiles through a recurrent neural network architecture. Their Integrate component, which reconciles potentially conflicting signals from different evidence sources, is conceptually analogous to the evidence integration function in this project that decides whether to override the LLM verdict based on fact-check API ratings.

## 2.4 Large Language Models for Fact-Checking

Brown et al. [31] introduced GPT-3 and demonstrated its few-shot learning capability, showing that sufficiently large language models can perform complex reasoning tasks from natural language prompts without task-specific fine-tuning. Their work established the paradigm of zero-shot and few-shot classification that this project exploits through structured prompts to Llama 3.3 70B.

Wei et al. [15] demonstrated that chain-of-thought prompting — asking models to reason step by step before arriving at a conclusion — significantly improves accuracy on knowledge-intensive tasks including fact verification. The structured prompt used in this project's Groq client, which asks the model to first identify FAKE or REAL indicators before stating its VERDICT, applies this principle to extract more reliable classifications from the language model.

Touvron et al. [3] introduced the Llama 2 family of open-weight language models and demonstrated that instruction-tuned versions achieve competitive performance on fact-checking and reasoning benchmarks compared to GPT-3.5. The selection of Llama 3.3 70B as the primary inference model in this project is motivated by this lineage of research, which establishes the 70B parameter scale as the threshold at which language models produce reliably structured output for fact verification tasks.

Lee et al. [32] cautioned that smaller language models (under 7B parameters) produce inconsistent structured output for tasks requiring binary classification with confidence scores. Their study found that models below 7B parameters fail to consistently follow structured output formats in up to 30% of cases. This finding directly motivated the design decision to treat Phi-3 Mini as a secondary fallback tier — used when the primary cloud model is unavailable — rather than the primary inference model, and to implement a robust multi-strategy response parser that handles malformed LLM outputs gracefully.

## 2.5 Heuristic and Linguistic Feature Analysis

Potthast et al. [5] conducted a stylometric analysis of hyperpartisan and fake news articles from 9 major publishers and identified consistent writing style differences. Fake news articles systematically use more hyperpartisan language, more clickbait structural patterns, more emotional amplifiers, and more first-person pronouns. Their comprehensive linguistic feature set directly informed the fake news indicator patterns in the heuristic engine, particularly the patterns targeting "you won't believe", "shocking truth", "they don't want you to know", and related clickbait formulations.

Horne and Adali [6] studied fake news at content and style levels and found that fake news article titles are more emotionally charged and contain significantly more pronouns and absolute quantifiers than legitimate news titles. They also found that fake news bodies are simpler and more repetitive, using a narrower vocabulary and more repetitive sentence structures. These findings are encoded in the heuristic engine through patterns targeting exaggeration markers ("100% guaranteed", "proven beyond doubt"), absolute quantifiers, and excessive punctuation patterns.

Castillo et al. [33] studied information credibility on Twitter and identified that source reputation, confirmation from other sources, and temporal patterns of information spread are the strongest predictors of credibility. Their work on automated credibility assessment from social context informed the trusted-source search strategy in this project, which uses the presence of matching articles in established news outlets as a credibility signal.

## 2.6 External Evidence and Fact-Check Verification

Vlachos and Riedel [34] introduced the task of computational fact-checking as a formal NLP problem and proposed using structured knowledge bases to verify extracted claims. Their work established the principle that external verification against a reference knowledge base is fundamentally different from and complementary to linguistic classification — the same principle underlying the fact-check API integration in this project.

Thorne and Vlachos [35] published the FEVER (Fact Extraction and VERification) dataset and shared task, which formalised fact-checking as a three-step pipeline: document retrieval, evidence extraction, and claim verification. Their finding that systems combining neural evidence retrieval with claim verification achieve substantially higher accuracy than claim-only systems supports the enrichment architecture of this project, where LLM predictions are augmented with external fact-check evidence that can override the model verdict when strong contradictory ratings are found.

Popat et al. [16] proposed DeClarE (Debunking Fake News and False Claims using Evidence-Aware Deep Learning), which jointly learns to assess claim credibility and identify relevant evidence from web articles. Their evidence integration approach, which weights evidence by source credibility and relevance to the claim, directly inspired the relevance scoring function in this project's trusted-source search, which assigns higher weight to articles with higher term-overlap relevance scores.

Nakamura et al. [36] introduced the r/Fakeddit dataset, a large-scale multimodal fake news detection benchmark containing over one million samples from Reddit. Their work highlighted the importance of considering both textual and visual modalities in fake news detection and noted that text-only classifiers achieve substantially lower recall on visually deceptive content. This finding motivates the OCR text cleaning pipeline in this project, which extracts text from screenshot images to enable analysis of visual fake news formats.

## 2.7 Sentiment Analysis in Misinformation

Ajao et al. [37] studied sentiment in social media misinformation and found that false claims exhibit significantly higher negative sentiment, higher emotional intensity, and more extreme polarity than true claims. Their results validated sentiment polarity as a useful supplementary feature for fake news detection, supporting its inclusion as a metadata field in every prediction response in this project.

Giachanou and Crestani [38] provided a comprehensive survey of sentiment-based approaches to fake news and opinion spam detection. They found that sentiment combined with linguistic features produces better results than either alone in low-resource settings, and noted that TextBlob's lexicon-based sentiment analysis provides a good balance between accuracy and computational cost for real-time applications. These findings support the use of TextBlob in the helpers module of this project.

Zubiaga et al. [39] studied rumour detection and resolution in social media and found that user responses expressing doubt, denial, or questioning are stronger predictors of rumour falsity than the linguistic features of the rumour text itself. While this project does not model user responses, their finding that emotional language in the original claim correlates with falsity is reflected in the emotional amplifier scoring in the heuristic engine.

## 2.8 NLP Preprocessing and Keyword Analysis

Bird et al. [40] developed NLTK (Natural Language Toolkit), which provides the tokenisation, stopword removal, and frequency analysis capabilities used in the preprocessing pipeline of this project. NLTK's word tokeniser handles punctuation splitting and contraction expansion, producing cleaner token sequences than simple whitespace splitting, which improves keyword extraction quality.

Muhammad et al. [41] applied deep learning to fake news detection and found that preprocessing quality — specifically stopword removal and lemmatisation — significantly impacts classifier performance. Their preprocessing pipeline, which includes URL removal, HTML tag stripping, and number normalisation, is implemented in the `clean_text()` function of the `preprocess.py` module.

## 2.9 Summary and Research Gap

The literature survey identifies the following key gaps that this project addresses:

| Identified Gap | Response in This Project |
|---|---|
| Fake news detection requires multiple signals [1][22] | Three-tier LLM + heuristic + external evidence architecture |
| Smaller LLMs produce unreliable structured output [32] | Llama 3.3 70B as primary tier; Phi-3 Mini as fallback only |
| Purely linguistic classifiers have accuracy ceiling [12][25] | Fact-check API can override LLM verdict with external evidence |
| No explainability in existing automated tools [11] | Structured multi-paragraph explanation returned with every verdict |
| Systems fail under model unavailability | Three independent fallback tiers with guaranteed heuristic baseline |
| No persistent history or user context | Full prediction history with search, filter, stats, and dashboard |
| Emotional language correlates with falsity [37][38] | Emotional amplifier scoring in heuristic engine |
| Domain-specific fake news requires tailored patterns [24] | 60+ Indian-context patterns (cricket, politics, health, finance) |
| External evidence boosts accuracy [35][16] | Parallel trusted-source RSS search across 12 verified domains |
| OCR fake news circulates as images [36] | OCR artefact cleaning pipeline before analysis |

---

# CHAPTER 3

# SOFTWARE REQUIREMENTS SPECIFICATIONS

## 3.1 Introduction

This chapter presents the Software Requirements Specification (SRS) for the AI-Based Fake News Detection System. The SRS defines the functional capabilities, non-functional properties, external interface requirements, and the hardware/software environment required to develop and operate the platform. The requirements are derived from the problem statement in Chapter 1 and the research gaps identified in Chapter 2.

The system operates in three primary contexts: as a real-time news classification engine accepting text submissions from authenticated users; as a user account management platform supporting registration, authentication, history, and personalisation; and as an administrative analytics interface providing platform governance for authorised administrators. Each context introduces distinct requirements, though the overall system presents them as a unified web application experience.

The requirements documented here reflect the complete implementation and have been validated against the deployed codebase. All functional requirements listed as implemented have been verified through the test suite documented in Chapter 7.

## 3.2 Functional Requirements

| FR ID | Requirement | Description |
|---|---|---|
| FR-01 | User Registration | The system shall allow users to register with a unique username, email address, and password of at least 6 characters. All fields shall be validated server-side before account creation. |
| FR-02 | Password Hashing | All user passwords shall be hashed using bcrypt before storage. Plaintext passwords shall never be persisted to the database. |
| FR-03 | User Authentication – Session | The system shall authenticate users via Flask server-side sessions for browser-based navigation, storing user_id, username, email, full_name, is_admin, and a JWT token in the session. |
| FR-04 | User Authentication – JWT | The system shall issue JWT access tokens on successful login, valid for 24 hours, for use by JavaScript API clients via the Authorization: Bearer header. |
| FR-05 | Dual Auth Support | All protected API routes shall accept both JWT header tokens and session-based authentication simultaneously, enabling seamless browser and API client operation. |
| FR-06 | Role-Based Access Control | Admin-only routes shall verify the is_admin flag in both the session and decoded JWT token before granting access. Non-admin users shall receive HTTP 403. |
| FR-07 | News Text Submission | The system shall accept news text submissions of at least 5 characters through the /api/predict/ endpoint via JSON POST. |
| FR-08 | OCR Text Cleaning | The system shall strip lines containing known news-logo source names shorter than 60 characters, remove character repetition, normalise spaced-out letter sequences, and remove non-standard characters from submitted text. |
| FR-09 | NLTK Preprocessing | The system shall preprocess every submission through a pipeline of URL removal, HTML stripping, punctuation removal, NLTK word tokenisation, and English stopword removal to extract keyword tokens. |
| FR-10 | Keyword Extraction | The system shall extract the top 10 most frequent non-stopword tokens from each submission using a frequency counter over the preprocessed token list. |
| FR-11 | Sentiment Analysis | The system shall compute a TextBlob sentiment polarity score for every submitted text and classify it as Positive (> 0.2), Negative (< −0.2), or Neutral. |
| FR-12 | Suspicious Phrase Detection | The system shall scan submitted text against 10 suspicious linguistic patterns covering sensationalism, clickbait, conspiracy language, viral manipulation, medical misinformation, urgency, and media distrust, and return a list of matched labels. |
| FR-13 | Three-Tier Inference | The system shall attempt LLM inference in the following order: (1) Groq Llama 3.3 70B if GROQ_API_KEY is set, (2) Ollama Phi-3 Mini if an Ollama server is reachable, (3) Heuristic pattern engine as guaranteed fallback. |
| FR-14 | Groq API Integration | When GROQ_API_KEY is configured, the system shall send a structured zero-shot fact-checking prompt to the llama-3.3-70b-versatile model with temperature 0.0 and parse VERDICT, CONFIDENCE, and EXPLANATION from the response. |
| FR-15 | Ollama Local Inference | When Ollama is reachable at localhost:11434, the system shall attempt inference using the phi3:mini model via both /api/chat and /api/generate endpoints, blacklisting vision models. |
| FR-16 | Heuristic Analysis | The system shall always run the pattern scoring engine as baseline analysis, returning a REAL or FAKE verdict with a confidence score derived from the weighted sum of matched fake and real indicator patterns. |
| FR-17 | Google Fact-Check Enrichment | The system shall query the Google Fact Check Tools API with key terms from the submission and use ratings containing "false", "misleading", "true", or "correct" to adjust the prediction and add ±8 to confidence. |
| FR-18 | Trusted Source Search | The system shall search 12 trusted Indian and international news domains via Google News RSS in parallel, using a ThreadPoolExecutor with 6 workers, and include matching articles with relevance ≥ 45% in the fact_checks output. |
| FR-19 | NewsAPI Integration | If NEWS_API_KEY is configured, the system shall query NewsAPI.org for articles matching key terms from the submission; otherwise the system shall fall back to BBC News and Google News RSS feeds. |
| FR-20 | Prediction History Save | Every successful prediction shall be saved to the news_history table (full analysis) and prediction_logs table (audit record) within the same database transaction. |
| FR-21 | History Retrieval | Authenticated users shall retrieve their prediction history with pagination (page, per_page), full-text search (ilike), prediction filter (REAL/FAKE), and sort by created_at, confidence, or prediction. |
| FR-22 | History Deletion | Authenticated users shall delete individual history entries or clear all their history. Each deletion shall be cascade-safe and session-rolled-back on error. |
| FR-23 | User Statistics | The system shall return total, real_count, fake_count, avg_confidence, text_total, image_total, and active_users statistics per authenticated user. |
| FR-24 | Admin Dashboard | The admin dashboard shall return total_users, active_users, total_predictions, total_history, real_count, fake_count, and recent_predictions (last 10) in a single API call. |
| FR-25 | Admin User Management | Administrators shall create, update, activate/deactivate, and delete regular user accounts. Deletion of admin accounts shall be blocked. All actions shall be logged to admin_logs. |
| FR-26 | Admin History Management | Administrators shall view all users' prediction history with pagination and search, and clear all records across all users. |
| FR-27 | Admin Timeline Stats | The admin panel shall expose a /api/admin/stats/timeline endpoint returning daily total and FAKE counts for a configurable number of past days. |
| FR-28 | Admin Method Stats | The admin panel shall return a breakdown of predictions by inference method (groq, ollama, heuristic) for platform-level model usage analysis. |
| FR-29 | Password Change | Authenticated users shall change their password by supplying their current password for verification and a new password of at least 6 characters. |
| FR-30 | Health Check Endpoint | The /api/health endpoint shall return the application status, Ollama availability, and version information without authentication. |

## 3.3 Non-Functional Requirements

| Non-Functional Requirement | Specification |
|---|---|
| Performance | Heuristic analysis response within 200 ms; Groq-based analysis within 4 seconds under normal load; Ollama-based analysis within 30 seconds. Analytics API response for cached data within 100 ms. |
| Availability | System shall remain fully operational for all core features (registration, authentication, prediction, history) without Groq API key, without Ollama, and without NewsAPI key. Heuristic fallback guarantees 100% prediction uptime. |
| Security | Passwords stored as bcrypt hashes (cost factor 12); JWT tokens expire after 24 hours; all admin routes protected by role verification on both session and JWT paths; article content endpoint rejects non-HTTP/HTTPS URLs; CORS restricted to API routes only. |
| Scalability | Flask application deployable via Gunicorn with multiple worker processes; SQLAlchemy connection pool configurable for high-concurrency environments; stateless JWT authentication enables horizontal scaling. |
| Usability | Multi-page navigation without context loss; mobile-responsive Tailwind CSS layout; flash messages for all form validation feedback; loading indicators during AI analysis. |
| Maintainability | Modular Flask blueprint architecture with clear separation between auth, prediction, history, and admin layers; all configuration via environment variables with documented defaults. |
| Testability | 70+ heuristic test cases in test_full.py; route-level validation via curl scripts; database migration handled automatically at startup; test coverage across all 10 subject categories. |
| Data Integrity | SQLAlchemy ORM with foreign key constraints and cascade delete rules; all write operations wrapped in try/except with session.rollback() on failure; column existence checks before schema-dependent queries. |
| Auditability | Every admin action logged to admin_logs with admin_id, action string, details, IP address, and timestamp; prediction_logs maintains lightweight audit record separate from full news_history. |

## 3.4 External Interfaces

### 3.4.1 Groq API

The system integrates with the Groq cloud API endpoint `https://api.groq.com/openai/v1/chat/completions` using the `llama-3.3-70b-versatile` model. The interface is a REST API accessed via HTTP POST with a Bearer token in the Authorization header. The model is invoked with `temperature: 0.0` to ensure deterministic output and `max_tokens: 400` to constrain response length. The API key is configured via the `GROQ_API_KEY` environment variable. If absent, the system skips this tier silently and proceeds to Ollama. The client implements a 15-second timeout and graceful handling of HTTP 4xx/5xx responses, returning None on any failure to trigger the next tier.

### 3.4.2 Ollama Local API

The optional Ollama integration connects to a locally running Ollama server at `http://localhost:11434`. The system first checks server availability by calling `/api/tags` with a 2-second timeout. On availability confirmation, it attempts inference using `phi3:mini` as the primary model and `tinyllama:latest` as a secondary local model. Both `/api/chat` and `/api/generate` endpoints are tried in sequence for maximum compatibility with different Ollama versions. Vision models are automatically detected by name pattern matching and blacklisted to prevent errors. All connection errors are caught and result in a silent fallback to the heuristic engine.

### 3.4.3 Google Fact Check Tools API

The system queries `https://toolbox.google.com/factcheck/api/v1/claimsearch` with the submission's key terms as the query parameter. This public API returns claim-review objects containing the claim text, textual rating (e.g., "False", "Misleading", "Mostly True"), and the reviewing organisation's name. Results are cached in a module-level dictionary keyed by the normalised query string to avoid redundant API calls within a session. The API is used without an API key, relying on public access rate limits.

### 3.4.4 NewsAPI.org

The optional NewsAPI integration queries `https://newsapi.org/v2/everything` with submission key terms, sorted by relevancy, filtered to English articles. Up to 5 articles are retrieved and included in the fact_checks array of the prediction response. The API key is configured via the `NEWS_API_KEY` environment variable. When absent, the system substitutes BBC News and Google News RSS feed parsing via feedparser, providing a keyless fallback with lower coverage.

### 3.4.5 Google News RSS

The trusted-source search function constructs Google News RSS URLs in the format `https://news.google.com/rss/search?q={query}+site:{domain}` for each of the 12 trusted domains. Responses are parsed using feedparser. Results are filtered by a relevance score function that computes term-overlap between the query and article title/summary, retaining only articles scoring ≥ 35%. A claim-anchor verification function further filters results by checking that key named entities in the claim appear in the article to prevent topic-adjacent but claim-irrelevant matches.

## 3.5 Hardware and Software Requirements

| Requirement Type | Specification |
|---|---|
| Minimum RAM | 4 GB (8 GB recommended when Ollama is used) |
| CPU | x86-64 multi-core; GPU optional (CUDA-compatible for Ollama acceleration) |
| Storage | Minimum 500 MB for application, database, and dependencies; additional 2–4 GB if Ollama models are downloaded locally |
| Operating System | Ubuntu 20.04+, macOS 12+, or Windows 10+ |
| Python Version | Python 3.10 or higher |
| Backend Framework | Flask 3.0.0, Gunicorn 21.2 |
| Authentication | Flask-JWT-Extended 4.6.0, Flask-Bcrypt 1.0.1 |
| Database ORM | Flask-SQLAlchemy 3.1.1 |
| Database (Dev) | SQLite (bundled with Python) |
| Database (Prod) | MySQL 8.0+ via PyMySQL 1.1.0 |
| NLP Libraries | NLTK 3.8.1, TextBlob (via PyPI), requests 2.31.0 |
| Web Scraping | BeautifulSoup4 4.12.2, lxml 4.9.4, feedparser (optional) |
| Environment Config | python-dotenv 1.0.0 |
| CORS | Flask-CORS 4.0.0 |
| Frontend | Jinja2 3.x (Flask built-in), Tailwind CSS (CDN) |
| Browser | Chrome 110+, Firefox 110+, Safari 15+ |

---

# CHAPTER 4

# SYSTEM ARCHITECTURE DESIGN

## 4.1 High-Level Architecture

The AI Fake News Detection System follows a layered three-tier architecture that cleanly separates the presentation layer, application logic layer, and data/model layer. This separation enables independent development, testing, and scaling of each layer without cascading changes across the codebase [42].

**Presentation Layer**: The presentation layer is a Jinja2-templated multi-page web application styled with Tailwind CSS and powered by vanilla JavaScript for asynchronous API interactions. The layer includes 13 HTML templates, a base template with shared navigation and footer components, and three JavaScript modules (api.js, main.js, dashboard.js). The JavaScript API client includes JWT token management, automatically attaching the stored token to all API requests as a Bearer header. The presentation layer communicates exclusively with the Flask application logic layer through the defined API endpoints; it has no direct database access.

**Application Logic Layer**: The Flask 3.0 backend is organised into four blueprints — `auth_bp`, `predict_bp`, `history_bp`, and `admin_bp` — each registered at a distinct URL prefix. The application factory pattern (`create_app()`) handles extension initialisation, blueprint registration, session decorator definition, and database seeding at startup. The core detection logic resides in `ollama_client.py`, which is the system's most complex module (1,364 lines) and orchestrates the three-tier inference pipeline, external enrichment layer, response formatting, and result caching. All configuration is externalised to environment variables with documented defaults in `config.py`.

**Data and Model Layer**: The data layer consists of a SQLite or MySQL relational database with five tables managed through SQLAlchemy ORM. No ML model weights are stored locally — inference is delegated to the Groq cloud API or the Ollama local server. The heuristic engine's pattern library is embedded in the application code as compiled Python regex objects, incurring zero I/O overhead at runtime. The application seeds default admin and demo users on first startup, making the system self-contained and immediately usable after installation.

## 4.2 System Context Diagram

The system context places the AI Fake News Detection System as a central processing platform interacting with five categories of external entities:

**End User**: Submits news text through browser forms and receives prediction results, explanation text, and enrichment evidence. Also interacts with the authentication system and prediction history.

**System Administrator**: Manages user accounts, monitors platform analytics, views admin action logs, and performs data maintenance through the admin panel UI.

**Groq Cloud API**: Receives structured fact-checking prompts and returns natural language responses containing VERDICT, CONFIDENCE, and EXPLANATION fields parsed by the Groq client module.

**Ollama Local Server**: Runs on the deployment machine alongside the Flask application, receiving inference requests via the localhost API and returning natural language responses.

**External Data Sources**: The Google Fact Check Tools API, Google News RSS feeds for 12 trusted domains, and optionally NewsAPI.org provide external evidence for the enrichment layer.

## 4.3 Technology Stack

| Layer / Concern | Technology |
|---|---|
| Backend Framework | Flask 3.0 (Python) with Gunicorn 21.2 WSGI server |
| Application Factory | Flask create_app() factory with blueprint registration |
| Authentication | Flask-JWT-Extended 4.6, Flask-Bcrypt 1.0, Flask server-side session |
| Primary LLM | Groq API, llama-3.3-70b-versatile model |
| Secondary LLM | Ollama local server, phi3:mini model |
| Fallback Analysis | Custom heuristic regex engine (60+ patterns, embedded in code) |
| NLP Preprocessing | NLTK 3.8 (tokenisation, stopwords), TextBlob (sentiment polarity) |
| News Enrichment | feedparser (RSS), requests (Fact Check API, NewsAPI, Groq API) |
| Concurrency | Python ThreadPoolExecutor for parallel trusted-source search |
| Database ORM | Flask-SQLAlchemy 3.1 with declarative base models |
| Database (Dev/Prod) | SQLite (dev) / MySQL 8.0 via PyMySQL 1.1 (production) |
| HTML Templating | Jinja2 (Flask built-in) |
| Styling | Tailwind CSS (CDN), custom CSS in static/css/style.css |
| Client-side JS | Vanilla JavaScript: api.js (JWT API calls), main.js (UI), dashboard.js (charts) |
| HTML Parsing | BeautifulSoup4 4.12, lxml 4.9 |
| CORS | Flask-CORS 4.0 (restricted to /api/* routes) |
| Environment Config | python-dotenv 1.0 with config.py defaults |
| Deployment | Gunicorn + python-dotenv; optional Nginx reverse proxy |

## 4.4 Data Flow Architecture

### 4.4.1 Prediction Data Flow

The prediction data flow begins when the user submits a news article text through the `/detect` page. The Tailwind-styled form POSTs a JSON body to the Flask `/api/predict/` endpoint through the JavaScript API client (`api.js`), which attaches the stored JWT token as the Authorization header. The `predict_news()` route handler validates the payload, verifies minimum text length, and begins processing. The text is first passed through `clean_ocr_text()`, which strips news logo watermarks and normalises OCR artefacts. The cleaned text is then processed through three parallel NLP operations: `preprocess_text()` and `extract_keywords()` from the ml module, and `analyze_sentiment()` plus `find_suspicious_phrases()` from the utils module. These operations produce the linguistic metadata fields returned alongside the prediction.

The cleaned text is then passed to `analyze_with_phi3()`, which launches the three-tier inference pipeline and enrichment layer. The function returns a comprehensive result dictionary containing the final prediction, confidence, structured explanation, fact check evidence, category, inference method, and trusted source count. This result, combined with the linguistic metadata, is saved to the database in a single transaction and returned as a JSON response. The JavaScript client renders the result in the detection page's result panel without a full page reload, displaying the verdict badge, confidence percentage, explanation text, keyword chips, sentiment label, and the fact-check evidence table.

### 4.4.2 Three-Tier Inference Data Flow

Inside `analyze_with_phi3()`, the enrichment layer runs first and in parallel: `_google_fact_check()` queries the Fact Check Tools API, `_search_trusted_sources()` dispatches 12 concurrent RSS requests via ThreadPoolExecutor, and `_heuristic_only_analysis()` computes the pattern-based baseline — all before any LLM call is made, since these are fast operations.

The Groq client is then invoked. If `GROQ_API_KEY` is set and the API returns a 200 response within 15 seconds, `_parse_verdict()` extracts the verdict using multi-strategy regex parsing. If the verdict is clearly REAL or FAKE, it is accepted. If Groq fails for any reason, `_call_ollama()` is invoked, which first checks Ollama availability with a 2-second health check before attempting inference. If Ollama also fails, the heuristic baseline result is used.

After the LLM tier resolves, the enrichment layer's results are applied. If the Google Fact Check API returned ratings containing "false" or "misleading", the prediction is forced to FAKE and confidence is boosted by 8 points. If ratings contain "true" or "correct", the prediction is forced to REAL with the same confidence boost. Trusted source matches with relevance ≥ 45% add 3 points to REAL confidence. The final structured explanation is assembled by `_verdict_explanation()`, which weaves together the LLM reasoning, fact-check evidence, and trusted source titles into a multi-paragraph human-readable justification.

### 4.4.3 Authentication Data Flow

The authentication system supports two parallel paths. For browser-based navigation, the login form POSTs credentials to the Flask `/login` route, which queries the users table, verifies the bcrypt hash via `check_password()`, and on success sets a Flask server-side session containing all user metadata and a JWT token. Subsequent page loads read the session and pass it to templates via the `inject_session()` context processor. For JavaScript API calls, the JWT token stored in the session is extracted by `api.js` and attached as an Authorization header. The `get_current_user_id()` helper in protected blueprints accepts either path, decoding the JWT token if present or reading `flask_session.get("user_id")` as fallback.

## 4.5 Blueprint and Module Structure

```
backend/
├── app.py               ← Flask factory, template routes, session decorators
├── config.py            ← Config class: SECRET_KEY, DB URI, JWT settings
├── ollama_client.py     ← Core inference engine (1364 lines)
├── groq_client.py       ← Groq API client
├── routes/
│   ├── auth.py          ← /api/auth/* : signup, login, profile, password
│   ├── predict.py       ← /api/predict/* : prediction endpoint, OCR cleaner
│   ├── history.py       ← /api/history/* : CRUD + stats
│   └── admin.py         ← /api/admin/* : users, history, logs, stats
├── models/
│   ├── __init__.py      ← db, bcrypt, jwt initialisation
│   ├── user.py          ← User, AdminLog models
│   ├── news.py          ← NewsHistory, Dataset models
│   └── prediction.py    ← PredictionLog model
├── ml/
│   └── preprocess.py    ← clean_text, tokenize, remove_stopwords, extract_keywords
└── utils/
    ├── helpers.py       ← analyze_sentiment, find_suspicious_phrases
    └── news_api.py      ← NewsAPI.org helper
```

---

# CHAPTER 5

# DETAILED DESIGN

## 5.1 Use Case Diagram

The system supports two primary actors: the **End User** who registers an account and interacts with detection and history features; and the **Administrator** who has all end-user capabilities plus governance functions over the entire user base and platform data.

**End User Use Cases:**
- UC-01: Register a new account with username, email, and password
- UC-02: Log in using username or email and password
- UC-03: Log out and clear the server-side session
- UC-04: Submit a news article text for analysis
- UC-05: View the prediction verdict, confidence, explanation, and evidence
- UC-06: View sentiment analysis and keyword extraction results
- UC-07: Browse paginated prediction history
- UC-08: Search history by keyword in news text
- UC-09: Filter history by REAL or FAKE prediction
- UC-10: Delete an individual history entry
- UC-11: Clear all personal history
- UC-12: View dashboard statistics (totals, ratios, average confidence)
- UC-13: Change account password

**Administrator Use Cases (all End User UCs plus):**
- UC-14: View platform-level analytics dashboard
- UC-15: List all registered users with search
- UC-16: Create a new user account
- UC-17: Edit user details (full name, email, password)
- UC-18: Activate or deactivate a user account
- UC-19: Delete a user account and all associated records
- UC-20: View all users' prediction history
- UC-21: Clear all prediction history platform-wide
- UC-22: View admin action audit log
- UC-23: View prediction timeline chart (daily totals for last N days)
- UC-24: View inference method breakdown statistics
- UC-25: View top-10 most active users by prediction volume

## 5.2 Class Diagram

### Backend Models

| Class | Key Attributes | Key Methods |
|---|---|---|
| User | id, username, email, password_hash, full_name, is_admin, is_active, created_at, updated_at | set_password(pwd), check_password(pwd), to_dict() |
| NewsHistory | id, user_id, news_text, prediction, confidence, explanation, sentiment, sentiment_score, keywords, suspicious_phrases, source_url, source_type, processing_time, method, created_at | to_dict() |
| PredictionLog | id, user_id, news_text (500 chars), prediction, confidence, method, processing_time, ip_address, created_at | to_dict() |
| AdminLog | id, admin_id, action, details, ip_address, created_at | to_dict() |
| Dataset | id, name, description, file_path, total_samples, is_active, created_at | to_dict() |

### Inference Engine Functions (ollama_client.py)

| Function | Return Type | Responsibility |
|---|---|---|
| analyze_with_phi3(text) | Dict[str, Any] | Main orchestrator: inference + enrichment + response assembly |
| _call_ollama(prompt) | Optional[str] | Sends structured prompt to local Ollama server |
| _try_inference(model, prompt) | Optional[str] | Tries chat then generate endpoints; blacklists vision models |
| _heuristic_only_analysis(text) | Dict[str, Any] | 60+ pattern scoring; returns verdict, confidence, explanation, category |
| _google_fact_check(query) | Optional[List[Dict]] | Queries Fact Check API with LRU cache |
| _search_trusted_sources(text) | List[Dict] | Parallel RSS search across 12 domains with ThreadPoolExecutor |
| _fetch_google_news_search(text, query, source) | List[Dict] | Single-domain RSS fetch with relevance + claim-anchor filtering |
| _search_news(query) | List | NewsAPI.org search with cache |
| _fetch_rss_news(query) | List | BBC + Google News RSS fallback |
| _parse_verdict(text) | Optional[str] | Multi-strategy regex verdict extraction from LLM response |
| _extract_confidence(text) | float | Regex confidence extraction; defaults to 88.0 |
| _extract_explanation(text) | str | Multi-format explanation extraction from LLM response |
| _classify_category(text) | str | Keyword-based category detection |
| _verdict_explanation(...) | str | Assembles structured multi-paragraph explanation |
| _relevance_score(query, title) | float | Term-overlap relevance scoring 0–100 |
| _meaningful_query_words(query) | set | Stopword-filtered word set extraction |
| _claim_anchor_terms(text) | List[str] | Named entity anchor extraction for claim verification |
| _source_matches_claim(text, title) | bool | Validates article matches specific claim |
| _build_search_query(text) | str | Extracts optimised search terms from submission |
| _clean_sentence(text, limit) | str | Cleans and truncates a sentence for explanation inclusion |
| check_ollama_status() | Dict[str, Any] | Returns running status and available model list |

## 5.3 Sequence Diagrams

### 5.3.1 Prediction Sequence (Complete)

```
Browser           api.js          Flask /predict     analyze_with_phi3    Database
   │                │                   │                    │                │
   │──form submit──▶│                   │                    │                │
   │                │──POST /api/predict/│                   │                │
   │                │   + JWT header    │                    │                │
   │                │                  │──clean_ocr_text()  │                │
   │                │                  │──preprocess_text() │                │
   │                │                  │──extract_keywords()│                │
   │                │                  │──analyze_sentiment()│               │
   │                │                  │──find_suspicious_phrases()          │
   │                │                  │──────────────────▶ │                │
   │                │                  │  analyze_with_phi3(text)            │
   │                │                  │                    │─fact_check()   │
   │                │                  │                    │─trusted_src()  │
   │                │                  │                    │─heuristic()    │
   │                │                  │                    │─groq_client()  │
   │                │                  │                    │  (or ollama)   │
   │                │                  │                    │─merge results  │
   │                │                  │◀────result dict────│                │
   │                │                  │──────────────────────────────────▶ │
   │                │                  │  db.session.add(NewsHistory)        │
   │                │                  │  db.session.add(PredictionLog)      │
   │                │                  │  db.session.commit()                │
   │                │◀──JSON result────│                    │                │
   │◀─render result─│                   │                    │                │
```

### 5.3.2 Login Sequence

```
Browser          Flask /login         User Model         Session
   │                  │                    │                │
   │──POST username───▶│                   │                │
   │    password       │──query by username/email──▶        │
   │                   │◀──── User object ─────────         │
   │                   │──check_password(pwd)──▶            │
   │                   │◀── True/False ─────────            │
   │                   │──create_access_token()             │
   │                   │──────────────────────────────────▶ │
   │                   │   set session[user_id, username,   │
   │                   │   is_admin, jwt_token]             │
   │◀── redirect /dashboard ──│           │                │
```

### 5.3.3 Admin User Toggle Sequence

```
Admin Browser    api.js         /api/admin/users/<id>/toggle   AdminLog
     │             │                       │                       │
     │─click toggle▶│                      │                       │
     │             │─POST + JWT admin─────▶│                       │
     │             │                       │──get_admin_id()       │
     │             │                       │──User.query.get(id)   │
     │             │                       │──user.is_active = !x  │
     │             │                       │──db.session.commit()  │
     │             │                       │──log_admin_action()──▶│
     │             │                       │   db.session.add(log) │
     │             │◀─── 200 user.to_dict()│                       │
     │◀─update UI──│                       │                       │
```

## 5.4 Activity Diagram — Complete Inference Decision Flow

The complete inference decision flow for a single prediction request proceeds as follows. After text cleaning and NLP preprocessing, the system simultaneously initiates fact-check enrichment and heuristic analysis. These operations run while the main inference pipeline begins.

The main inference pipeline first checks whether a GROQ_API_KEY environment variable is set. If set, the system constructs the structured fact-checking prompt and calls the Groq API with a 15-second timeout. On a successful HTTP 200 response, `_parse_verdict()` attempts extraction using four strategies in sequence: structured VERDICT: field matching, leading line classification, negation handling ("NOT FAKE" → REAL), and keyword frequency counting (counting REAL vs FAKE occurrences). If a clear verdict is extracted, it is accepted as the LLM prediction. If the response is ambiguous or Groq fails, the system proceeds to the Ollama tier.

The Ollama path performs a health check against `localhost:11434/api/tags` with a 2-second timeout. If the Ollama server is running, the system iterates through available models starting with phi3:mini, tries both `/api/chat` and `/api/generate` endpoints, and applies the same verdict parsing pipeline. If Ollama also fails, the heuristic baseline result from the parallel computation is used directly.

After the LLM tier resolves, the enrichment results are applied. If the fact-check API returned strong negative ratings (containing "false", "misleading", "hoax", "incorrect"), the prediction is forced to FAKE regardless of the LLM result, and confidence is boosted by 8 percentage points up to 99%. If positive ratings are found ("true", "correct", "accurate", "factual"), the prediction is forced to REAL with the same confidence boost. Trusted source matches boost REAL confidence by 3 points. The final explanation is assembled and the complete result dictionary is returned.

## 5.5 Database Design

The system uses a relational SQLite (development) or MySQL (production) database with five interrelated tables.

### 5.5.1 Entity-Relationship Overview

The `users` table is the central entity. The `news_history` and `prediction_logs` tables hold user-generated prediction records and reference `users` via foreign keys with cascade delete behaviour — when a user is deleted, all their history is automatically removed. The `admin_logs` table records administrator actions and references `users` via a non-cascade foreign key, preserving log entries for account history review. The `datasets` table is a standalone catalogue for training dataset management and has no foreign key relationships.

### 5.5.2 Table: users

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | Primary key |
| username | VARCHAR(80) | NOT NULL, UNIQUE | Login username |
| email | VARCHAR(120) | NOT NULL, UNIQUE | Email address |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash (cost 12) |
| full_name | VARCHAR(150) | NULL | Display name |
| is_admin | BOOLEAN | DEFAULT FALSE | Admin role flag |
| is_active | BOOLEAN | DEFAULT TRUE | Account active flag |
| created_at | DATETIME | DEFAULT NOW | Registration timestamp |
| updated_at | DATETIME | ON UPDATE NOW | Last modification |

### 5.5.3 Table: news_history

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | Primary key |
| user_id | INT | FK(users.id), CASCADE DELETE | Owning user |
| news_text | TEXT | NOT NULL | Full submitted text |
| prediction | VARCHAR(10) | NOT NULL | "REAL" or "FAKE" |
| confidence | FLOAT | NOT NULL | 0.0–100.0 confidence |
| explanation | TEXT | NULL | Full structured explanation |
| sentiment | VARCHAR(20) | NULL | Positive/Negative/Neutral |
| sentiment_score | FLOAT | NULL | TextBlob polarity score |
| keywords | TEXT | NULL | Comma-separated keywords |
| suspicious_phrases | TEXT | NULL | Comma-separated phrase labels |
| source_url | VARCHAR(500) | NULL | Optional source URL |
| source_type | VARCHAR(20) | DEFAULT 'text' | "text" or "image" |
| processing_time | FLOAT | NULL | Seconds for analysis |
| method | VARCHAR(50) | DEFAULT 'phi3' | Inference method used |
| created_at | DATETIME | DEFAULT NOW | Submission timestamp |

### 5.5.4 Table: prediction_logs

| Column | Type | Description |
|---|---|---|
| id | INT, PK | Primary key |
| user_id | INT, FK | Reference to user (nullable for anonymous) |
| news_text | VARCHAR(500) | First 500 chars of submission |
| prediction | VARCHAR(10) | REAL or FAKE |
| confidence | FLOAT | Confidence score |
| method | VARCHAR(50) | Inference method label |
| processing_time | FLOAT | Processing duration in seconds |
| ip_address | VARCHAR(45) | Client IP for audit |
| created_at | DATETIME | Log timestamp |

### 5.5.5 Table: admin_logs

| Column | Type | Description |
|---|---|---|
| id | INT, PK | Primary key |
| admin_id | INT, FK(users.id) | Administrator who performed the action |
| action | VARCHAR(255) | Short action description |
| details | TEXT | Full action details |
| ip_address | VARCHAR(45) | Admin client IP |
| created_at | DATETIME | Action timestamp |

### 5.5.6 Database Indexes

The schema defines the following indexes for query performance:

- `idx_email` and `idx_username` on users for O(log n) login lookups
- `idx_user_id` and `idx_prediction` and `idx_created_at` on news_history for filtered history queries
- `idx_admin_id` and `idx_created_at` on admin_logs for audit log pagination
- Composite query optimisation is provided by SQLAlchemy's ORM query builder, which generates parameterised SQL with automatic index utilisation.

## 5.6 Module-Level Design

### 5.6.1 Heuristic Pattern Engine — Fake Indicator Categories

The heuristic engine implements 60+ compiled regex patterns organised into semantic categories. Each matched pattern adds 1 to the fake_score, with emotional amplifiers contributing 2 if 3 or more emotional words are found. The pattern categories and their linguistic basis are:

| Category | Pattern Count | Research Basis | Example Pattern |
|---|---|---|---|
| Clickbait language | 8 | Potthast et al. [5] | "you won't believe", "one simple trick" |
| Conspiracy claims | 6 | Horne and Adali [6] | "deep state", "illuminati", "new world order" |
| Health misinformation | 5 | Rashkin et al. [23] | "vaccine microchip", "5G causes COVID" |
| Sports role mismatch | 5 | Domain-specific | "Dhoni RCB player", "Kohli CSK" |
| Political hoaxes | 6 | Castillo et al. [33] | "Modi resign", "PM dies", "election rigged" |
| Financial scams | 4 | Conroy et al. [25] | "double your money", "guaranteed returns" |
| Anti-expert language | 4 | Rashkin et al. [23] | "doctors hate", "scientists hiding" |
| Pseudoscience | 5 | Shu et al. [1] | "flat earth", "perpetual motion", "quantum healing" |
| Vague sourcing | 3 | Horne and Adali [6] | "sources say", "anonymous sources" |
| Urgency / panic | 4 | Potthast et al. [5] | "urgent alert", "this is not a drill" |
| Persecution complex | 4 | Allcott and Gentzkow [20] | "wake up sheeple", "they can't handle the truth" |
| Viral manipulation | 3 | Vosoughi et al. [2] | "pass this on", "send this to 10 people" |
| Death/resignation hoaxes | 4 | Domain-specific | "President dead", "CM arrested" |
| Historical denial | 2 | Domain-specific | "holocaust hoax", "genocide myth" |
| Communal violence | 3 | Domain-specific | "temple attack", "mass killing" |

### 5.6.2 Heuristic Pattern Engine — Real Indicator Categories

| Category | Pattern Count | Research Basis | Example Pattern |
|---|---|---|---|
| Credible source citations | 1 (multi-source) | Popat et al. [16] | "according to Reuters", "BBC reported" |
| Peer-reviewed references | 1 | Thorne and Vlachos [35] | "study published in Nature", "Lancet study" |
| Official source statements | 1 | Castillo et al. [33] | "government spokesperson", "court ruled" |
| Law enforcement confirmation | 1 | Castillo et al. [33] | "police confirmed", "FBI investigation" |
| Verified data citations | 1 | Zhou et al. [22] | "according to data from", "statistics released by" |
| Named official statements | 1 | Rashkin et al. [23] | "minister stated", "department released" |

### 5.6.3 OCR Text Cleaner Design

The `clean_ocr_text()` function in `routes/predict.py` addresses a specific problem: users who photograph news headlines or screenshot WhatsApp forwards capture not only the article text but also embedded watermarks, logo text, and other artefacts that confuse the LLM with spurious source indicators [36]. The function:

1. Splits the text into lines and removes any line whose lowercase form contains a known news source name (from a 74-entry list covering Indian and international outlets) and whose length is less than 60 characters, targeting short logo-only lines while preserving longer sentences that happen to mention a news outlet.
2. Collapses runs of 4+ repeated characters to 3 (removing "AAAAAAA" artefacts).
3. Detects and collapses single-letter spacing patterns (OCR output for large fonts) using a two-pass regex.
4. Removes non-printable and non-ASCII-printable characters that produce encoding errors.
5. Normalises multiple consecutive dots, spaces before punctuation, and multiple spaces.

