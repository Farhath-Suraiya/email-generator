document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const btnModeGen = document.getElementById("btn-mode-gen");
  const btnModeEval = document.getElementById("btn-mode-eval");
  const referenceReplyGroup = document.getElementById("reference-reply-group");
  const incomingEmailInput = document.getElementById("incoming-email");
  const referenceReplyInput = document.getElementById("reference-reply");
  
  const btnSubmit = document.getElementById("btn-submit");
  const btnSubmitText = document.getElementById("btn-submit-text");
  const btnClear = document.getElementById("btn-clear");
  const btnCopy = document.getElementById("btn-copy");

  // States
  const stateEmpty = document.getElementById("state-empty");
  const stateLoading = document.getElementById("state-loading");
  const stateError = document.getElementById("state-error");
  const stateContent = document.getElementById("state-content");
  
  const errorMessage = document.getElementById("error-message");
  const responseText = document.getElementById("response-text");
  
  // Evaluation Card Elements
  const evaluationCard = document.getElementById("evaluation-card");
  const overallScoreNum = document.getElementById("overall-score-num");
  const overallBadge = document.getElementById("overall-badge");
  const evalExplanation = document.getElementById("eval-explanation");
  
  const valSemantic = document.getElementById("val-semantic");
  const fillSemantic = document.getElementById("fill-semantic");
  
  const valRelevance = document.getElementById("val-relevance");
  const fillRelevance = document.getElementById("fill-relevance");
  
  const valCompleteness = document.getElementById("val-completeness");
  const fillCompleteness = document.getElementById("fill-completeness");
  
  const valTone = document.getElementById("val-tone");
  const fillTone = document.getElementById("fill-tone");
  
  const valFactuality = document.getElementById("val-factuality");
  const fillFactuality = document.getElementById("fill-factuality");
  
  const wrapperStrengths = document.getElementById("wrapper-strengths");
  const wrapperIssues = document.getElementById("wrapper-issues");
  const retrievedList = document.getElementById("retrieved-list");
  const exampleCount = document.getElementById("example-count");

  let currentMode = "gen"; // 'gen' or 'eval'

  // Mode Switchers
  btnModeGen.addEventListener("click", () => {
    currentMode = "gen";
    btnModeGen.classList.add("active");
    btnModeEval.classList.remove("active");
    referenceReplyGroup.classList.add("hidden");
    btnSubmitText.textContent = "Generate Suggested Reply";
  });

  btnModeEval.addEventListener("click", () => {
    currentMode = "eval";
    btnModeEval.classList.add("active");
    btnModeGen.classList.remove("active");
    referenceReplyGroup.classList.remove("hidden");
    btnSubmitText.textContent = "Generate & Evaluate";
  });

  btnClear.addEventListener("click", () => {
    incomingEmailInput.value = "";
    referenceReplyInput.value = "";
    showState("empty");
  });

  btnCopy.addEventListener("click", () => {
    const textToCopy = responseText.textContent;
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      const originalText = btnCopy.innerHTML;
      btnCopy.innerHTML = "<span>Copied!</span>";
      setTimeout(() => {
        btnCopy.innerHTML = originalText;
      }, 2000);
    }
  });

  function showState(state) {
    stateEmpty.classList.add("hidden");
    stateLoading.classList.add("hidden");
    stateError.classList.add("hidden");
    stateContent.classList.add("hidden");
    btnCopy.classList.add("hidden");

    if (state === "empty") stateEmpty.classList.remove("hidden");
    if (state === "loading") stateLoading.classList.remove("hidden");
    if (state === "error") stateError.classList.remove("hidden");
    if (state === "content") {
      stateContent.classList.remove("hidden");
      btnCopy.classList.remove("hidden");
    }
  }

  // Form Submit Handler
  btnSubmit.addEventListener("click", async () => {
    const incomingEmail = incomingEmailInput.value.trim();
    const referenceReply = referenceReplyInput.value.trim();

    if (!incomingEmail) {
      alert("Please enter an incoming email.");
      incomingEmailInput.focus();
      return;
    }

    if (currentMode === "eval" && !referenceReply) {
      alert("Please enter a ground truth reference reply for Evaluation Mode.");
      referenceReplyInput.focus();
      return;
    }

    showState("loading");

    try {
      let endpoint = "/generate";
      let payload = { email: incomingEmail };

      if (currentMode === "eval") {
        endpoint = "/generate-and-evaluate";
        payload = {
          incoming_email: incomingEmail,
          reference_reply: referenceReply
        };
      }

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Server error processing request.");
      }

      const data = await response.json();
      renderResults(data);
      showState("content");

    } catch (err) {
      errorMessage.textContent = err.message;
      showState("error");
    }
  });

  function renderResults(data) {
    // 1. Render Suggested Response
    responseText.textContent = data.suggested_reply || "";

    // 2. Render Retrieved Examples
    const examples = data.retrieved_examples || [];
    exampleCount.textContent = examples.length;
    retrievedList.innerHTML = "";

    examples.forEach((ex, idx) => {
      const card = document.createElement("div");
      card.className = "example-card";
      const scorePct = (ex.score * 100).toFixed(1);
      
      card.innerHTML = `
        <div class="example-header">
          <span class="cat-badge">Example ${idx + 1} • ${ex.category}</span>
          <span class="score-badge">Similarity: ${scorePct}%</span>
        </div>
        <div class="ex-label">INCOMING HISTORICAL EMAIL:</div>
        <div class="ex-text">${escapeHtml(ex.incoming_email)}</div>
        <div class="ex-label">HISTORICAL REFERENCE REPLY:</div>
        <div class="ex-text">${escapeHtml(ex.reference_reply)}</div>
      `;
      retrievedList.appendChild(card);
    });

    // 3. Render Evaluation (If present)
    if (data.evaluation) {
      evaluationCard.classList.remove("hidden");
      const ev = data.evaluation;
      
      overallScoreNum.textContent = ev.overall_score.toFixed(1);
      evalExplanation.textContent = ev.overall_explanation || "";

      // Metric Bars
      setMetric(valSemantic, fillSemantic, ev.semantic_similarity?.score);
      setMetric(valRelevance, fillRelevance, ev.relevance?.score);
      setMetric(valCompleteness, fillCompleteness, ev.completeness?.score);
      setMetric(valTone, fillTone, ev.tone?.score);
      setMetric(valFactuality, fillFactuality, ev.factual_consistency?.score);

      // Strengths & Issues Tags
      renderTags(wrapperStrengths, ev.strengths || [], "tag-strength");
      renderTags(wrapperIssues, ev.issues || [], "tag-issue");

    } else {
      evaluationCard.classList.add("hidden");
    }
  }

  function setMetric(valElem, fillElem, score) {
    if (score === undefined || score === null) {
      valElem.textContent = "N/A";
      fillElem.style.width = "0%";
      return;
    }
    const val = score.toFixed(1);
    valElem.textContent = `${val} / 100`;
    fillElem.style.width = `${val}%`;

    // Color indicators
    if (score >= 80) fillElem.style.backgroundColor = "var(--success)";
    else if (score >= 50) fillElem.style.backgroundColor = "var(--warning)";
    else fillElem.style.backgroundColor = "var(--danger)";
  }

  function renderTags(container, tagList, className) {
    container.innerHTML = "";
    if (!tagList || tagList.length === 0) {
      container.innerHTML = '<span class="field-help">None identified</span>';
      return;
    }
    tagList.forEach(text => {
      const tag = document.createElement("span");
      tag.className = `tag ${className}`;
      tag.textContent = text;
      container.appendChild(tag);
    });
  }

  function escapeHtml(str) {
    return (str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
