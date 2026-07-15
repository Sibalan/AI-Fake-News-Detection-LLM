var analyzeBtn = document.getElementById('analyze-btn');
var newsText = document.getElementById('news-text');
var sourceUrl = document.getElementById('source-url');

function analyzeNews() {
  var text = newsText.value.trim();
  if (!text) {
    showToast('Please enter news text to analyze', 'error');
    return;
  }
  if (text.length < 5) {
    showToast('Please enter at least 5 characters', 'error');
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<div class="spinner"></div> Analyzing...';

  var resultDiv = document.getElementById('result-container');
  resultDiv.innerHTML = '<div class="text-center py-12"><div class="spinner mx-auto mb-4" style="width:2.5rem;height:2.5rem;border-width:3px"></div><p class="text-dark-400">Phi-3 LLM is analyzing your news content...</p></div>';
  resultDiv.classList.remove('hidden');

  var data = { text: text };
  if (sourceUrl.value.trim()) {
    data.source_url = sourceUrl.value.trim();
  }

  apiPost('/api/predict/', data)
    .then(function(r) { return r.json(); })
    .then(function(result) {
      if (result.error) {
        resultDiv.innerHTML = '<div class="card border-2 border-red-500/30 text-center py-8"><i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-4"></i><p class="text-red-400">' + result.error + '</p></div>';
        showToast(result.error, 'error');
        return;
      }
      displayResult(result);
      loadStats();
      loadRecentHistory();
    })
    .catch(function(err) {
      resultDiv.innerHTML = '<div class="card border-2 border-red-500/30 text-center py-8"><i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-4"></i><p class="text-red-400">Analysis failed. Is Ollama running?</p></div>';
      showToast('Analysis failed. Check if Ollama is running.', 'error');
    })
    .finally(function() {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = '<i class="fas fa-shield-alt"></i> Analyze News';
    });
}

function displayResult(result) {
  var displayPred = result.display_prediction || result.prediction;
  var isReal = displayPred === 'REAL';
  var borderColor = isReal ? 'border-emerald-500/30' : 'border-red-500/30';
  var badgeClass = isReal ? 'badge-real' : 'badge-fake';
  var badgeIcon = isReal ? 'fa-check-circle' : 'fa-times-circle';
  var confidenceColor = isReal ? 'text-emerald-400' : 'text-red-400';
  var barColor = isReal ? 'bg-emerald-500' : 'bg-red-500';

  var suspiciousHtml = '';
  if (result.suspicious_phrases && result.suspicious_phrases.length > 0) {
    var tags = result.suspicious_phrases.map(function(p) {
      return '<span class="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-full">' + p + '</span>';
    }).join('');
    suspiciousHtml = '<div class="mt-4"><p class="text-dark-500 text-xs mb-2">SUSPICIOUS PATTERNS</p><div class="flex flex-wrap gap-1">' + tags + '</div></div>';
  }

  var keywordsHtml = '';
  if (result.keywords && result.keywords.length > 0) {
    var kws = result.keywords.map(function(kw) {
      return '<span class="px-3 py-1 bg-dark-700/50 text-dark-300 text-sm rounded-lg border border-dark-600/30">' + kw + '</span>';
    }).join('');
    keywordsHtml = '<div class="mt-4"><p class="text-dark-500 text-xs mb-2"><i class="fas fa-hashtag text-primary-400 mr-1"></i>KEYWORDS DETECTED</p><div class="flex flex-wrap gap-2">' + kws + '</div></div>';
  }

  var sentimentBadge = result.sentiment === 'Positive' ? 'bg-emerald-500/20 text-emerald-400' :
                        result.sentiment === 'Negative' ? 'bg-red-500/20 text-red-400' :
                        'bg-dark-600/30 text-dark-300';

  var html = '<div class="card border-2 ' + borderColor + ' animate-fade-in">' +
      '<div class="flex items-center justify-between mb-6">' +
      '<h2 class="text-xl font-bold text-white">Analysis Result</h2>' +
      '<div class="flex items-center gap-2">' +
        '<span class="' + badgeClass + '"><i class="fas ' + badgeIcon + ' mr-1"></i> ' + displayPred + ' NEWS</span>' +
        (result.is_misleading ? '<span class="cred-moderate ml-2 text-xs px-3 py-1 rounded-full">Misleading</span>' : '') +
      '</div>' +
    '</div>' +
    '<div class="grid sm:grid-cols-2 gap-6 mb-6">' +
      '<div>' +
        '<p class="text-dark-400 text-sm mb-2">Confidence</p>' +
        '<div class="flex items-center gap-4">' +
          '<div class="flex-1 h-3 bg-dark-700 rounded-full overflow-hidden">' +
            '<div class="h-full rounded-full ' + barColor + ' transition-all duration-1000" style="width:' + result.confidence + '%"></div>' +
          '</div>' +
          '<span class="text-2xl font-bold ' + confidenceColor + '">' + result.confidence + '%</span>' +
        '</div>' +
      '</div>' +
      '<div class="grid grid-cols-2 gap-4">' +
        '<div class="glass rounded-xl p-3 text-center">' +
          '<i class="fas fa-microchip text-primary-400 text-lg mb-1"></i>' +
          '<p class="text-dark-500 text-xs">Method</p>' +
          '<p class="text-white text-sm font-medium">Phi-3 LLM</p>' +
        '</div>' +
        '<div class="glass rounded-xl p-3 text-center">' +
          '<i class="fas fa-clock text-primary-400 text-lg mb-1"></i>' +
          '<p class="text-dark-500 text-xs">Time</p>' +
          '<p class="text-white text-sm font-medium">' + result.processing_time + 's</p>' +
        '</div>' +
      '</div>' +
    '</div>' +
    '<div class="mb-6">' +
      '<p class="text-dark-400 text-sm mb-2"><i class="fas fa-info-circle text-primary-400 mr-1"></i> AI Explanation</p>' +
      '<div class="glass rounded-xl p-4"><p class="text-dark-200 text-sm leading-relaxed">' + result.explanation + '</p></div>' +
    '</div>' +
    '<div class="grid sm:grid-cols-3 gap-4">' +
        '<div>' +
          '<p class="text-dark-500 text-xs mb-2">RESULT SUMMARY</p>' +
          '<div class="flex items-center gap-4">' +
            '<div style="width:96px;height:96px;position:relative">' +
              '<svg width="96" height="96" viewBox="0 0 100 100" style="transform:rotate(-90deg)">' +
                '<circle cx="50" cy="50" r="40" fill="none" stroke="rgba(71,85,105,0.18)" stroke-width="8"></circle>' +
                '<circle cx="50" cy="50" r="40" fill="none" stroke="' + (isReal ? '#34d399' : '#ef4444') + '" stroke-width="8" stroke-linecap="round" stroke-dasharray="251.2" stroke-dashoffset="' + (251.2 - (result.confidence / 100) * 251.2) + '" class="conf-ring"></circle>' +
              '</svg>' +
              '<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">' +
                '<span style="font-size:1.25rem;font-weight:800;color:' + (isReal ? '#34d399' : '#ef4444') + '">' + result.confidence + '%</span>' +
                '<span class="text-dark-500 text-xs">Confidence</span>' +
              '</div>' +
            '</div>' +
            '<div class="flex-1">' +
              '<p class="text-white text-lg font-semibold mb-1">' + (isReal ? 'Real News' : 'Fake News') + '</p>' +
              '<p class="text-dark-400 text-sm mb-3">' + (isReal ? 'Supported by trusted sources and AI verification.' : 'Flagged by AI and fact-check signals — review carefully.') + '</p>' +
              '<div class="w-full bg-dark-700/50 rounded-full h-2 overflow-hidden mb-2"><div style="width:' + result.confidence + '%;background:linear-gradient(90deg,#4ade80,#6366f1);height:100%"></div></div>' +
              '<div class="flex gap-3 text-xs text-dark-400">' +
                '<div class="flex items-center gap-1"><i class="fas fa-newspaper text-indigo-400"></i><span>' + (result.trusted_source_count || 0) + ' sources</span></div>' +
                '<div class="flex items-center gap-1"><i class="fas fa-check-double text-emerald-400"></i><span>' + ((result.fact_checks && result.fact_checks.length) || 0) + ' fact-checks</span></div>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<div>' +
          '<p class="text-dark-500 text-xs mb-2">WORDS</p>' +
          '<div class="bg-dark-700/50 rounded-lg px-3 py-2 text-white text-sm">' + result.word_count + ' tokens</div>' +
        '</div>' +
        '<div>' +
          '<p class="text-dark-500 text-xs mb-2">METHOD</p>' +
          '<div class="bg-dark-700/50 rounded-lg px-3 py-2 text-white text-sm">' + (result.method || 'Phi-3') + '</div>' +
        '</div>' +
      '</div>' +
    suspiciousHtml +
    getFactChecksHtml(result) +
    keywordsHtml +
  '</div>';

  document.getElementById('result-container').innerHTML = html;
  var resultContainer = document.getElementById('result-container');
  resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

}
}

function getFactChecksHtml(result) {
  if (!result.fact_checks || result.fact_checks.length === 0) return '';
  var items = result.fact_checks.map(function(fc) {
    var ratingColor = 'text-yellow-400';
    var rating = (fc.rating || '').toLowerCase();
    if (rating.includes('false') || rating.includes('fake') || rating.includes('misleading')) ratingColor = 'text-red-400';
    else if (rating.includes('true') || rating.includes('correct') || rating.includes('accurate')) ratingColor = 'text-emerald-400';
    return '<div class="glass rounded-xl p-3 flex items-start gap-3">' +
      '<i class="fas fa-check-double text-primary-400 mt-1"></i>' +
      '<div class="flex-1 min-w-0">' +
        '<p class="text-dark-200 text-sm truncate">' + (fc.claim || '') + '</p>' +
        '<div class="flex items-center gap-2 mt-1">' +
          '<span class="' + ratingColor + ' text-xs font-medium">' + (fc.rating || 'Referenced') + '</span>' +
          (fc.source ? '<span class="text-dark-500 text-xs">via ' + fc.source + '</span>' : '') +
        '</div>' +
      '</div></div>';
  }).join('');
  return '<div class="mt-4"><p class="text-dark-500 text-xs mb-2"><i class="fas fa-check-double text-primary-400 mr-1"></i>EXTERNAL FACT CHECKS</p><div class="space-y-2">' + items + '</div></div>';
}

function loadStats() {
  apiGet('/api/history/stats')
    .then(function(r) { return r.json(); })
    .then(function(stats) {
      if (stats.error) return;
      var el = document.getElementById('stats-panel');
      if (!el) return;
      el.innerHTML =
        '<div class="card"><h3 class="text-lg font-bold text-white mb-4">Your Stats</h3>' +
        '<div class="space-y-4">' +
          '<div class="flex justify-between items-center"><span class="text-dark-400 text-sm">Total Analyses</span><span class="text-2xl font-bold text-white">' + stats.total + '</span></div>' +
          '<div class="flex justify-between items-center"><span class="text-dark-400 text-sm"><i class="fas fa-check-circle text-emerald-400 mr-1"></i> Real</span><span class="text-xl font-bold text-emerald-400">' + stats.real_count + '</span></div>' +
          '<div class="flex justify-between items-center"><span class="text-dark-400 text-sm"><i class="fas fa-exclamation-triangle text-red-400 mr-1"></i> Fake</span><span class="text-xl font-bold text-red-400">' + stats.fake_count + '</span></div>' +
          '<div class="flex justify-between items-center pt-2 border-t border-dark-600/30"><span class="text-dark-400 text-sm">Avg Confidence</span><span class="text-xl font-bold gradient-text">' + stats.avg_confidence + '%</span></div>' +
        '</div></div>';
    });
}

function loadRecentHistory() {
  apiGet('/api/history/?per_page=5&sort_by=created_at&sort_order=desc')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      var el = document.getElementById('recent-history');
      if (!el) return;
      var items = data.history || [];
      if (items.length === 0) {
        el.innerHTML = '<div class="card"><h3 class="text-lg font-bold text-white mb-4">Recent Activity</h3><p class="text-dark-400 text-center py-4">No analysis history yet.</p></div>';
        return;
      }
      var html = '<div class="card"><h3 class="text-lg font-bold text-white mb-4">Recent Activity</h3><div class="space-y-3">';
      items.forEach(function(item) {
        var badge = item.prediction === 'REAL' ? 'text-emerald-400' : 'text-red-400';
        html += '<div class="glass rounded-xl p-4 flex items-center justify-between">' +
          '<div class="flex-1 min-w-0 mr-4"><p class="text-dark-200 text-sm truncate">' + item.news_text + '</p><p class="text-dark-500 text-xs mt-1">' + formatDate(item.created_at) + '</p></div>' +
          '<div class="flex items-center gap-3 shrink-0"><span class="text-sm font-bold ' + badge + '">' + item.prediction + '</span><span class="text-dark-400 text-xs">' + item.confidence + '%</span></div>' +
        '</div>';
      });
      html += '</div></div>';
      el.innerHTML = html;
    });
}
