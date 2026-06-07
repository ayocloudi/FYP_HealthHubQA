# HealthHubQA - Presentation & Viva Prep Guide
## How to Present Your FYP for a 1:1 Grade

---

## PART 1: YOUR 3-MINUTE ELEVATOR PITCH (Learn This By Heart)

Say this naturally, like you're telling a friend:

> "My project is about making AI safer in healthcare. You know how ChatGPT sometimes
> makes stuff up? That's called a hallucination. Now imagine that happening when a
> doctor or patient asks a medical question — it could be dangerous.
>
> So I built a system called HealthHubQA that tests whether giving AI real medical
> research papers to read BEFORE answering (that's called RAG - Retrieval Augmented
> Generation) actually makes it more accurate and less likely to hallucinate.
>
> I tested 5 different AI models — from small local ones to GPT-4 — and found that
> RAG improved GPT-4's accuracy by 24 percentage points. But here's the interesting
> finding: not all models benefit equally. One model actually got WORSE with RAG.
> That's a real research contribution — it shows RAG isn't a magic fix for everyone."

---

## PART 2: SLIDE-BY-SLIDE PRESENTATION GUIDE

### Slide 1: Title Slide
**What to say:** "My project investigates how to detect and reduce hallucinations in
AI systems used for healthcare question answering."

### Slide 2: The Problem (WHY this matters)
**Simple explanation:**
- "AI models like ChatGPT sometimes generate confident-sounding answers that are
  completely wrong — these are called hallucinations"
- "In healthcare, a wrong answer could lead to wrong treatment decisions"
- "My project asks: Can we make these models more truthful by giving them real
  medical evidence to read first?"

**Real-world example to give:**
> "Imagine asking an AI: 'Is metformin used to treat hypertension?' A hallucinating
> AI might say 'Yes, metformin lowers blood pressure.' But that's WRONG — metformin
> is for diabetes. My system would first retrieve actual medical papers about
> metformin, then give them to the AI, so it answers correctly."

### Slide 3: What is RAG? (Your KEY concept)
**Explain like this:**
> "Think of it like an open-book exam vs a closed-book exam.
>
> WITHOUT RAG = closed-book: The AI answers purely from memory. It might remember
> wrong or make things up.
>
> WITH RAG = open-book: Before answering, the AI searches a library of real medical
> papers, finds the 3 most relevant ones, reads them, and THEN answers. This
> 'grounds' the answer in real evidence."

**Technical detail (for supervisor):**
- Retriever uses sentence-transformer embeddings (all-MiniLM-L6-v2)
- Creates 384-dimensional vectors of each medical document
- Uses cosine similarity to find the top-3 most relevant passages
- These passages are injected into the AI's prompt as context

### Slide 4: Your Experimental Design
**Simple version:**
> "I set up a fair test. I took 5 different AI models and tested each one twice:
> once WITHOUT any help (no-RAG), and once WITH retrieved medical papers (RAG).
> That gives me 10 experiments total. I used 100 real medical questions from
> PubMedQA — a trusted medical research dataset."

**The 5 models (know these):**

| Model | Simple Description | Why You Chose It |
|-------|-------------------|-----------------|
| Flan-T5 | Small, instruction-following AI by Google | Free, lightweight, good baseline |
| GPT-4 | OpenAI's most powerful model | Gold standard, best commercial AI |
| BioBART | AI specially trained on medical text | Tests if medical pre-training helps |
| DistilBART | Lightweight summarisation model | Tests a weaker architecture |
| Phi-3 Mini | Microsoft's small but smart model | Tests if small local models can compete |

### Slide 5: Your Pipeline (How It Works)
**Walk through the flow:**
```
Question comes in
    ↓
[RETRIEVER] Searches 500 medical documents, finds top 3 matches
    ↓
[GENERATOR] AI model reads question + 3 documents, generates answer
    ↓
[EVALUATOR] Compares AI's answer to the known correct answer
    ↓
[METRICS] Records accuracy, F1, precision, recall
```

### Slide 6: RESULTS (Your Most Important Slide)

**Present this table and explain each row:**

| Model | Without RAG | With RAG | Change | What This Means |
|-------|-----------|---------|--------|----------------|
| GPT-4 | 40% | **64%** | **+24%** | RAG massively helps the best model |
| Flan-T5 | 40% | **55%** | **+15%** | RAG helps instruction-tuned models |
| Phi-3 Mini | 30% | **75%** | **+45%** | Biggest RAG improvement (small sample) |
| BioBART | 58% | **58%** | **0%** | Already medical-trained, RAG adds nothing |
| DistilBART | 39% | **32%** | **-7%** | RAG actually HURTS this model |

**How to explain each finding simply:**

1. **GPT-4 (+24%):** "The smartest model benefits hugely from evidence. Like giving
   a smart student a textbook — they know how to use it."

2. **Flan-T5 (+15%):** "Even a smaller model improves with evidence, just not as much."

3. **Phi-3 (+45%):** "The biggest jump! But caveat: only 20 samples due to my laptop's
   RAM limits. The trend is promising but needs more data to confirm."

4. **BioBART (0% change):** "This model was already trained on medical papers, so it
   already 'knows' the medical domain. RAG doesn't add new information it didn't
   already have. This proves medical pre-training is powerful on its own."

5. **DistilBART (-7%):** "THIS is my most interesting finding. RAG actually made it
   WORSE. Why? Because DistilBART is a summarisation model — when you give it long
   medical contexts, it gets confused. Not every model can handle extra information.
   This shows RAG is NOT a one-size-fits-all solution."

### Slide 7: Key Findings / Research Contributions
Present these 4 points:

1. **RAG significantly reduces hallucination risk for instruction-tuned models**
   - GPT-4 accuracy jumped from 40% to 64%
   
2. **Model architecture determines RAG benefit**
   - Instruction-tuned models (GPT-4, Flan-T5) benefit most
   - Summarisation models (DistilBART) can be hurt by RAG
   
3. **Domain pre-training is a strong alternative to RAG**
   - BioBART achieved 58% without any retrieval — competitive with RAG-enhanced models
   
4. **Practical constraints shape deployment decisions**
   - RAM, latency, API costs all matter in real healthcare settings
   - Phi-3 needed only 2.2GB RAM vs Llama's 4.6GB

### Slide 8: Challenges & How You Solved Them
**Pick 3-4 of these (shows problem-solving skills):**

| Problem | How You Solved It |
|---------|------------------|
| FAISS library crashed with NumPy 2.x | Switched to sklearn cosine similarity — same results, more stable |
| Llama 3 needed more RAM than laptop had | Found Phi-3 Mini (2.2GB instead of 4.6GB) — still competitive |
| GPT API key ran out of credits | Added error handling so experiments continued without crashing |
| T5 tokenizer broke with new Transformers version | Replaced with BioBART — actually better for medical domain |
| API key accidentally exposed | Immediately revoked, switched to environment variables |

### Slide 9: Literature Connection
**Show you READ the papers:**
- "Lewis et al. (2020) introduced RAG — I implemented their approach for healthcare"
- "Zuo & Jiang (2025) created MedHallBench — my evaluation follows similar principles"
- "Ji et al. (2023) proposed self-reflection — a future extension for my system"
- "Asgari et al. (2025) framework for clinical safety — inspired my safety-aware design"

### Slide 10: Future Work
- Self-reflection loops (the AI checks its own answer before outputting)
- Larger datasets (MedQA, MedMCQA) for cross-domain testing
- Streamlit/Flask web interface for live demo
- Human hallucination annotation (template already created)
- Fine-tuning models specifically for medical QA

### Slide 11: Conclusion
> "I proved that RAG can significantly reduce hallucinations for the right models,
> but it's not universal. The choice of model architecture matters as much as the
> retrieval strategy. For real-world healthcare AI, we need BOTH good retrieval
> AND the right model to make AI trustworthy."

---

## PART 3: QUESTIONS THEY WILL DEFINITELY ASK (With Answers)

### Category A: Understanding Your Work

**Q1: "What exactly is a hallucination in the context of LLMs?"**
> "It's when the AI generates text that sounds confident and fluent but is factually
> wrong or not supported by any source. In healthcare, this could mean inventing
> drug interactions or making up statistics about treatment outcomes."

**Q2: "Why did you choose PubMedQA specifically?"**
> "Three reasons: (1) It's a trusted, peer-reviewed medical QA dataset used in many
> papers. (2) It has yes/no/maybe labels, which makes evaluation straightforward.
> (3) It includes the original research abstracts as context, which is perfect for
> testing retrieval systems."

**Q3: "Why these 5 models? Why not just use GPT-4?"**
> "I wanted to compare different architectures to see if the benefits of RAG are
> universal. GPT-4 is behind a paid API — not everyone can use it. I tested local
> models (Flan-T5, BioBART, Phi-3) to see if free, privacy-preserving alternatives
> could work. The variety revealed that architecture matters — which wouldn't show
> with just one model."

**Q4: "Explain your retrieval process step by step."**
> "Step 1: I convert all 500 medical abstracts into numerical vectors using a
> sentence transformer (all-MiniLM-L6-v2).
> Step 2: When a question comes in, I convert it to a vector too.
> Step 3: I calculate cosine similarity between the question vector and all 500
> document vectors.
> Step 4: I pick the top 3 most similar documents.
> Step 5: I give those 3 documents plus the question to the AI model."

**Q5: "Why cosine similarity and not something else?"**
> "I originally planned to use FAISS (Facebook's similarity search library), but
> it had a compatibility issue with NumPy 2.x on my system. Cosine similarity from
> scikit-learn gives identical results at this scale (500 documents). FAISS would
> matter more for millions of documents."

### Category B: Challenging Your Results

**Q6: "Your accuracy numbers seem low — 64% for GPT-4 is not great. Why?"**
> "Two reasons: (1) PubMedQA is genuinely hard — even human doctors disagree on
> some answers, especially 'maybe' questions. Published baselines for PubMedQA are
> around 50-70% for most models. (2) My label extraction uses keyword matching
> (looking for 'yes', 'no', 'maybe' in the generated text), which sometimes
> misclassifies longer answers. The key finding isn't the absolute numbers — it's
> the RELATIVE improvement from RAG."

**Q7: "Phi-3 got 75% but only on 20 samples. Isn't that unreliable?"**
> "Yes, the small sample size means we should be cautious about that number. I
> acknowledge this limitation. I used only 20 samples because Phi-3 runs locally
> on CPU and each question took about 60 seconds. The 45% improvement is a strong
> SIGNAL worth investigating further, but I wouldn't claim it as a definitive
> result. With more compute resources, I'd run all 100 samples."

**Q8: "Why did RAG hurt DistilBART?"**
> "DistilBART is a distilled model originally trained for summarisation, not QA.
> When given extra retrieval context, it tried to summarise the context rather than
> answer the question. The additional text essentially confused it. This is actually
> a valuable finding — it shows that RAG requires models that can FOLLOW
> INSTRUCTIONS about how to use retrieved context."

**Q9: "BioBART didn't improve with RAG. Doesn't that undermine your thesis?"**
> "Actually, it SUPPORTS my thesis. It shows that the problem of hallucination can
> be addressed in different ways. BioBART was pre-trained on biomedical literature,
> so it already has medical knowledge baked in. RAG helps models that LACK domain
> knowledge. This reveals that there are multiple paths to reducing hallucination:
> either better pre-training OR better retrieval."

**Q10: "How do you actually MEASURE hallucination?"**
> "In this project, I measure it indirectly through accuracy — if the model gives
> a wrong answer (says 'yes' when it should be 'no'), that's evidence of
> hallucination. I also created a hallucination annotation template where I can
> manually check if answers are grounded in the retrieved context. For a more
> comprehensive approach, metrics like FACTSCORE and ACHMI exist, which I discuss
> as future work."

### Category C: Technical Deep-Dives

**Q11: "What is a sentence transformer and how does embedding work?"**
> "A sentence transformer converts text into a list of numbers (a vector) that
> captures its meaning. Similar sentences get similar numbers. I used all-MiniLM-L6-v2,
> which creates a 384-number vector for each piece of text. When I find the cosine
> similarity between a question's vector and a document's vector, a score near 1.0
> means they're about the same topic."

**Q12: "What's the difference between TF-IDF and your embedding approach?"**
> "TF-IDF counts word frequency — it matches documents by shared words. My embedding
> approach understands MEANING. For example, 'heart attack' and 'myocardial
> infarction' would score low with TF-IDF (different words) but high with embeddings
> (same meaning). For medical text where synonyms are common, embeddings are better."

**Q13: "Could you explain your experimental methodology?"**
> "I used a 2×5 experimental grid: 2 conditions (with RAG and without RAG) crossed
> with 5 models. I kept the same 100 questions for all models (except Phi-3 which
> used 20 due to compute limits). I measured accuracy, macro F1-score, precision,
> and recall. Each experiment is fully logged in CSV files for reproducibility."

**Q14: "What is F1-score and why is it important here?"**
> "F1-score combines precision (how many of the model's 'yes' answers were actually
> yes) and recall (how many actual 'yes' answers did the model find). It's important
> because PubMedQA has an unbalanced dataset — more 'yes' answers than 'no' or
> 'maybe'. A model could get decent accuracy by just always saying 'yes', but its
> F1-score would show it's failing on the other classes."

**Q15: "Why didn't you use FAISS as originally planned?"**
> "FAISS had a runtime error with NumPy version 2.x — specifically, it tried to
> access numpy._core which was removed in newer NumPy versions. Since my dataset is
> only 500 documents, sklearn's cosine similarity is just as fast. FAISS would be
> essential if I scaled to millions of documents."

### Category D: Critical Thinking & Reflection

**Q16: "What would you do differently if you started again?"**
> "Three things: (1) I'd set up a proper GPU environment from day one — running
> Phi-3 on CPU limited my sample size. (2) I'd implement proper hallucination
> metrics like FACTSCORE from the start, not just accuracy. (3) I'd start with
> more models simultaneously rather than adding them one by one, to avoid
> refactoring my code each time."

**Q17: "What are the ethical implications of your work?"**
> "Healthcare AI has high stakes — a wrong answer could harm patients. My work
> shows that RAG helps but isn't perfect (64% is still wrong 36% of the time).
> This means healthcare AI should ALWAYS have human oversight. My system should
> assist clinicians, never replace them. Also, I only used publicly available
> datasets — no patient data was involved."

**Q18: "How does your work compare to existing literature?"**
> "Most existing work (like MedHallBench) focuses on benchmarking hallucination
> rates on static datasets. My work adds a COMPARATIVE study across multiple
> models with and without RAG, showing that the benefit varies by architecture.
> The finding that DistilBART gets worse with RAG hasn't been widely reported."

**Q19: "How would you deploy this in a real hospital?"**
> "I'd recommend: (1) Use a medical-specific model like BioBART for baseline,
> enhanced with RAG. (2) Add a confidence threshold — if the model isn't sure,
> it should say 'I don't know' rather than guess. (3) Always show the retrieved
> sources so doctors can verify. (4) Run it as a decision-support tool, not an
> autonomous system."

**Q20: "What's your main research contribution?"**
> "My main contribution is demonstrating that RAG's effectiveness for hallucination
> mitigation depends on model architecture. This challenges the common assumption
> that RAG is universally beneficial. I showed it helps instruction-tuned models
> (GPT-4: +24%), is neutral for domain-pretrained models (BioBART: 0%), and can
> hurt unsuitable architectures (DistilBART: -7%)."

### Category E: Specific Technical Questions

**Q21: "What prompt template did you use for RAG?"**
> "For RAG, the prompt was: 'Based on the following medical context: [retrieved
> passages]. Answer the question: [question]. Respond with yes, no, or maybe.'
> For no-RAG, I simply asked: 'Answer the following medical question: [question].
> Respond with yes, no, or maybe.'"

**Q22: "How did you handle the 'maybe' class?"**
> "PubMedQA has three classes: yes, no, and maybe. 'Maybe' means the evidence is
> inconclusive. This makes it harder than binary classification. Most models
> struggle with 'maybe' because they tend to commit to yes or no. My confusion
> matrices show this — 'maybe' has the lowest recall across all models."

**Q23: "What happens if the retriever gets the wrong documents?"**
> "That's a great question. If the retriever pulls irrelevant documents, the model
> could hallucinate based on wrong context — that's even worse than no context.
> I logged the top-1 and mean similarity scores for every query so I can check
> retrieval quality. In future work, a 'retrieval confidence threshold' could
> reject low-quality retrievals."

**Q24: "What is the computational cost?"**
> "Local models (Flan-T5, BioBART) take about 1-3 seconds per question. Phi-3
> takes about 60 seconds on CPU. GPT-4 takes about 2-5 seconds but costs money
> per API call. For 100 samples, the full pipeline takes roughly 15-30 minutes
> for local models, much longer for Phi-3 on CPU."

---

## PART 4: TIPS FOR A 1:1 GRADE

### What Examiners Look For:

1. **Deep understanding** — Don't just describe WHAT you did, explain WHY
2. **Critical analysis** — Acknowledge limitations honestly
3. **Original insight** — Your DistilBART finding is genuinely interesting
4. **Technical competence** — Show you understand the code, not just ran it
5. **Literature awareness** — Connect your findings to published papers
6. **Professional presentation** — Confident, clear, well-structured

### Power Phrases to Use:

- "My results suggest that..." (not "My results prove that...")
- "An interesting finding was..." (shows critical thinking)
- "A limitation of this approach is..." (shows self-awareness)
- "Building on the work of Lewis et al. (2020)..." (shows you read papers)
- "If I had more time/compute, I would..." (shows you thought ahead)
- "The practical implication is..." (shows real-world thinking)

### Body Language & Delivery:

- **Slow down** on key findings (the results table)
- **Make eye contact** with both the supervisor and second reader
- **Point at your graphs** when discussing results
- **Pause after key findings** to let them absorb
- **If you don't know an answer:** "That's an interesting question. Based on my
  understanding, I'd say... but I'd need to investigate further to be certain."

### Common Mistakes to Avoid:

- DON'T read from slides
- DON'T apologise for limitations — present them as insights
- DON'T rush through results — they're your MAIN contribution
- DON'T use jargon without explaining it
- DON'T say "I just followed a tutorial" — emphasise YOUR design decisions

---

## PART 5: QUICK REFERENCE CARD (Print This Out)

### Your Numbers:
- **5 models tested** (Flan-T5, GPT-4, BioBART, DistilBART, Phi-3)
- **10 experimental conditions** (5 models × 2 conditions)
- **500 PubMedQA documents** in the retrieval index
- **100 test questions** per model (20 for Phi-3)
- **17 Python scripts** written
- **2,500+ lines of code**
- **Best result:** GPT-4 + RAG = 64% accuracy
- **Biggest improvement:** Phi-3 + RAG = +45% (small sample)
- **Most interesting finding:** DistilBART WORSE with RAG (-7%)
- **Embedding model:** all-MiniLM-L6-v2 (384 dimensions)
- **Retrieval:** Top-3 cosine similarity

### Your 3 Key Messages:
1. RAG reduces hallucinations for instruction-tuned models
2. Not all models benefit — architecture matters
3. Domain pre-training (BioBART) is a viable alternative to RAG

### Your Unique Contribution:
"A comparative multi-model analysis showing RAG's hallucination mitigation 
effectiveness varies by model architecture — challenging the assumption 
that RAG universally improves medical QA systems."
