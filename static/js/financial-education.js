/**
 * E-Cüzdan — Financial Education & Interactive Academy JS
 */

const feI18n = window.ECuzdanI18n || {};

// Quiz functionality
let currentQuiz = null;
let currentQuizDifficulty = 'beginner';
let currentAnswers = {};

async function startQuiz(difficulty) {
    try {
        const response = await fetch(ECuzdanEndpoints.education.quizStart, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || '',
            },
            body: JSON.stringify({ difficulty })
        });
        
        const data = await response.json();
        
        if (window.ECuzdanApi && window.ECuzdanApi.dto && typeof window.ECuzdanApi.dto.achievements === 'function') {
            window.ECuzdanApi.dto.achievements(data);
        }
        if (data.success) {
            currentQuiz = data.quiz_id;
            currentQuizDifficulty = difficulty;
            currentAnswers = {};
            displayQuizQuestions(data.questions);
        } else {
            alert(data.error || feI18n.fe_quiz_start_error || 'Quiz başlatılamadı');
        }
    } catch (error) {
        console.error('Quiz başlatma hatası:', error);
        alert(feI18n.fe_quiz_start_request_error || 'Quiz başlatılırken bir ağ hatası oluştu');
    }
}

function displayQuizQuestions(questions) {
    const quizContainer = document.createElement('div');
    quizContainer.className = 'fixed inset-0 bg-black/50 flex items-start justify-center z-50 overflow-y-auto p-4';
    quizContainer.id = 'quiz-modal';
    quizContainer.setAttribute('role', 'dialog');
    quizContainer.setAttribute('aria-modal', 'true');
    quizContainer.setAttribute('aria-labelledby', 'quizModalTitle');
    
    const quizTitle = feI18n.fe_tab_quiz || 'Quiz';
    const questionCountText = questions.length + ' ' + (feI18n.fe_quiz_question_count || 'Soru');
    const submitText = feI18n.fe_quiz_submit || "Quiz'i Bitir";
    const cancelText = feI18n.tx_cancel_btn || 'İptal';

    quizContainer.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[calc(100vh-2rem)] overflow-y-auto">
            <div class="bg-gradient-to-r from-emerald-600 to-teal-600 p-6">
                <h2 id="quizModalTitle" class="text-2xl font-black text-white uppercase tracking-tight">${quizTitle}</h2>
                <p class="text-emerald-100 mt-2">${questionCountText}</p>
            </div>
            <div class="p-8">
                ${questions.map((q, index) => `
                    <div class="mb-8" data-question-id="${q.id}">
                        <p class="text-lg font-bold text-slate-800 mb-4">${index + 1}. ${q.question}</p>
                        <div class="space-y-3">
                            ${Object.entries(q.options).map(([key, value]) => `
                                <label class="flex items-center p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition">
                                    <input type="radio" name="question_${q.id}" value="${key}" class="mr-3" onchange="selectAnswer(${q.id}, '${key}')">
                                    <span class="text-slate-700">${value}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
                <button data-macro="button_secondary" type="button" onclick="submitQuiz()" class="w-full bg-emerald-600 text-white px-6 py-3 rounded-lg font-bold text-sm hover:bg-emerald-700 transition">${submitText}</button>
                <button data-macro="button_secondary" type="button" onclick="closeQuizModal()" class="w-full mt-3 bg-slate-200 text-slate-700 px-6 py-3 rounded-lg font-bold text-sm hover:bg-slate-300 transition">${cancelText}</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(quizContainer);
    document.body.classList.add('overflow-hidden');
    quizContainer.addEventListener('click', (event) => {
        if (event.target === quizContainer) closeQuizModal();
    });
    const firstInput = quizContainer.querySelector('input[type="radio"]');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 50);
    }
}

function selectAnswer(questionId, answer) {
    currentAnswers[questionId] = answer;
}

async function submitQuiz() {
    if (Object.keys(currentAnswers).length === 0) {
        alert(feI18n.fe_quiz_empty_answer || 'Lütfen en az bir soruyu cevaplayın.');
        return;
    }
    
    try {
        const response = await fetch(ECuzdanEndpoints.education.quizSubmit, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || '',
            },
            body: JSON.stringify({ 
                answers: currentAnswers,
                difficulty: currentQuizDifficulty
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayQuizResults(data);
        } else {
            alert(data.error || feI18n.fe_quiz_submit_error || 'Quiz değerlendirilemedi');
        }
    } catch (error) {
        console.error('Quiz gönderme hatası:', error);
        alert(feI18n.fe_quiz_submit_request_error || 'Quiz gönderilirken hata oluştu');
    }
}

function displayQuizResults(data) {
    const quizModal = document.getElementById('quiz-modal');
    if (!quizModal) return;
    const scoreColor = data.score >= 80 ? 'text-emerald-600' : (data.score >= 60 ? 'text-blue-600' : 'text-amber-600');
    const resultsTitle = feI18n.fe_quiz_results_title || 'Quiz Sonuçları';
    const correctAnswerLabel = feI18n.fe_quiz_correct_answer || 'Doğru Cevap';
    const closeBtnLabel = feI18n.fe_quiz_close || 'Kapat';

    quizModal.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[calc(100vh-2rem)] overflow-y-auto">
            <div class="bg-gradient-to-r from-blue-600 to-indigo-600 p-6">
                <h2 class="text-2xl font-black text-white uppercase tracking-tight">${resultsTitle}</h2>
            </div>
            <div class="p-8 text-center">
                <div class="text-6xl font-black ${scoreColor} mb-4">${data.score}%</div>
                <p class="text-slate-600 mb-6">${data.correct_count} / ${data.total_count} ${correctAnswerLabel}</p>
                
                <div class="space-y-4 mb-8 text-left">
                    ${(data.results || []).map(r => `
                        <div class="p-4 rounded-lg ${r.is_correct ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'}">
                            <p class="font-bold ${r.is_correct ? 'text-emerald-700' : 'text-red-700'}">
                                ${r.is_correct ? '✓' : '✗'} Soru ${r.question_id}
                            </p>
                            ${!r.is_correct ? `
                                <p class="text-sm text-slate-600 mt-2">${correctAnswerLabel}: ${r.correct_answer}</p>
                                ${r.explanation ? `<p class="text-sm text-slate-500 mt-1">${r.explanation}</p>` : ''}
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
                
                <button data-macro="button_secondary" type="button" onclick="closeQuizModal()" class="w-full sticky bottom-0 bg-blue-600 text-white px-6 py-3 rounded-lg font-bold text-sm hover:bg-blue-700 transition shadow-lg">${closeBtnLabel}</button>
            </div>
        </div>
    `;
}

function closeQuizModal() {
    const quizModal = document.getElementById('quiz-modal');
    if (quizModal) {
        quizModal.remove();
    }
    document.body.classList.remove('overflow-hidden');
    currentQuiz = null;
    currentAnswers = {};
}

function filterDictionaryTerms(query) {
    const q = (query || '').toLowerCase().trim();
    const cards = document.querySelectorAll('#dictionary-grid .dictionary-card');
    let visible = 0;
    cards.forEach(card => {
        const term = card.dataset.term || '';
        const desc = card.dataset.desc || '';
        const show = !q || term.includes(q) || desc.includes(q);
        card.style.display = show ? '' : 'none';
        if (show) visible++;
    });
    const countEl = document.getElementById('dictionary-count');
    if (countEl) countEl.textContent = `${visible} terim listelendi`;
}

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const quizModal = document.getElementById('quiz-modal');
        if (quizModal) {
            closeQuizModal();
            return;
        }
        const dictSearch = document.getElementById('dictionary-search');
        if (dictSearch && document.activeElement === dictSearch && dictSearch.value) {
            dictSearch.value = '';
            filterDictionaryTerms('');
        }
    }
});

// Progress tracking
function showProgressMessage(message) {
    const topicContainer = document.getElementById('topic-progress-container');
    if (topicContainer) {
        topicContainer.innerHTML = `<p class="text-slate-500 text-center">${message}</p>`;
    }
}

async function loadProgress() {
    try {
        const response = await fetch(ECuzdanEndpoints.education.progress);
        const data = await response.json();
        if (data.success) {
            updateProgressUI(Array.isArray(data.progress) ? data.progress : [], data.stats || {});
        } else {
            const container = document.getElementById('topic-progress-container');
            showProgressMessage(data.error || container?.dataset.progressError || feI18n.fe_progress_load_error || 'İlerleme yüklenemedi');
        }
    } catch (error) {
        console.error('İlerleme yükleme hatası:', error);
        const container = document.getElementById('topic-progress-container');
        showProgressMessage(container?.dataset.progressError || feI18n.fe_progress_load_error || 'İlerleme yüklenemedi');
    }
}

function updateProgressUI(progress, stats = {}) {
    const topicLabels = {
        income_expenses: feI18n.fe_topic_income_expenses || 'Gelir ve Gider Yönetimi',
        compound_interest: feI18n.fe_topic_compound_interest || 'Bileşik Getiri Gücü',
        assets: feI18n.fe_topic_assets || 'Varlık Sınıfları ve Karakteristikleri',
        financial_freedom: feI18n.fe_topic_financial_freedom || 'Finansal Özgürlük ve Güvenlik',
        investing: feI18n.fe_topic_investing || 'Yatırımın Temelleri',
        risk_management: feI18n.fe_topic_risk_management || 'Risk Yönetimi ve Çeşitlendirme',
        portfolio_optimization: feI18n.fe_topic_portfolio_optimization || 'Modern Portföy Teorisi',
        behavioral_finance: feI18n.fe_topic_behavioral_finance || 'Davranışsal Finans ve Psikoloji',
        tax_planning: feI18n.fe_topic_tax_planning || 'Vergi Planlaması ve Verimlilik',
        retirement_planning: feI18n.fe_topic_retirement_planning || 'Emeklilik Planlaması',
        international_investing: feI18n.fe_topic_international_investing || 'Uluslararası Yatırım',
        derivatives: feI18n.fe_topic_derivatives || 'Türev Araçlar ve Hedge',
        alternative_investments: feI18n.fe_topic_alternative_investments || 'Alternatif Yatırımlar',
        quantitative_finance: feI18n.fe_topic_quantitative_finance || 'Kantitatif Finans Temelleri',
        algorithmic_trading: feI18n.fe_topic_algorithmic_trading || 'Algoritmik Alım-Satım',
        machine_learning_finance: feI18n.fe_topic_machine_learning_finance || 'Makine Öğrenmesi & Finans',
        blockchain_crypto: feI18n.fe_topic_blockchain_crypto || 'Blokzincir ve Kripto Varlıklar',
        esg_investing: feI18n.fe_topic_esg_investing || 'Sürdürülebilir Yatırım (ESG)'
    };

    // Update progress bars and stats
    const completedCount = Number.isFinite(stats.completed_topics)
        ? stats.completed_topics
        : progress.filter(p => p.completed).length;
    const avgProgress = Number.isFinite(stats.quiz_average)
        ? stats.quiz_average
        : (progress.length > 0
            ? Math.round(progress.reduce((sum, p) => sum + p.progress_percent, 0) / progress.length)
            : 0);
    const dayStreak = Number.isFinite(stats.day_streak) ? stats.day_streak : 0;
    
    // Update stats elements
    const completedElement = document.querySelector('.progress-stats[data-type="completed"]');
    const averageElement = document.querySelector('.progress-stats[data-type="average"]');
    const streakElement = document.querySelector('.progress-stats[data-type="streak"]');
    
    if (completedElement) {
        completedElement.textContent = completedCount;
    }
    if (averageElement) {
        averageElement.textContent = avgProgress + '%';
    }
    if (streakElement) {
        streakElement.textContent = dayStreak;
    }
    
    // Update topic progress bars
    const topicContainer = document.getElementById('topic-progress-container');
    if (topicContainer && progress.length > 0) {
        topicContainer.innerHTML = progress.map(p => {
            const colorClass = p.progress_percent >= 80 ? 'bg-emerald-600' : 
                              (p.progress_percent >= 50 ? 'bg-blue-600' : 
                              (p.progress_percent >= 25 ? 'bg-purple-600' : 'bg-amber-600'));
            const textColorClass = p.progress_percent >= 80 ? 'text-emerald-600' : 
                                  (p.progress_percent >= 50 ? 'text-blue-600' : 
                                  (p.progress_percent >= 25 ? 'text-purple-600' : 'text-amber-600'));
            
            return `
                <div class="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-bold text-slate-700">${topicLabels[p.topic] || p.topic}</span>
                        <span class="${textColorClass} font-bold">${p.progress_percent}%</span>
                    </div>
                    <div class="w-full bg-slate-200 rounded-full h-2">
                        <div class="${colorClass} h-2 rounded-full transition-all duration-500" style="width: ${p.progress_percent}%"></div>
                    </div>
                </div>
            `;
        }).join('');
    } else if (topicContainer) {
        topicContainer.innerHTML = `
            <div class="bg-slate-50 rounded-xl p-4 border border-slate-200">
                <p class="text-slate-500 text-center">${topicContainer.dataset.progressEmpty || 'No progress data available'}</p>
            </div>
        `;
    }
}

// Topic progress lifecycle: start on entry, autosave observed sections, and allow explicit completion.
async function loadTopicProgress() {
    const panel = document.querySelector('[data-topic-progress]');
    if (!panel) return;

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const topic = panel.dataset.topic;
    const phase = panel.dataset.phase;
    const stepNodes = Array.from(panel.closest('main, body').querySelectorAll('[data-progress-step]'));
    const state = {
        completedSteps: new Set(),
        progressPercent: 0,
        completed: false,
        lastPersisted: -1,
        inFlight: null,
        pending: null,
    };

    const statusElement = document.getElementById('topic-progress-status');
    const percentElement = document.getElementById('topic-progress-percent');
    const stepElement = document.getElementById('topic-progress-step');
    const barElement = document.getElementById('topic-progress-bar');
    const completeButton = document.getElementById('topic-complete-btn');
    const progressbar = panel.querySelector('[role="progressbar"]');

    const markCompleteLabel = feI18n.fe_progress_mark_complete || 'Tamamlandı Olarak İşaretle';

    const render = () => {
        const percent = state.completed ? 100 : state.progressPercent;
        if (percentElement) percentElement.textContent = `${percent}%`;
        if (stepElement) stepElement.textContent = `${state.completed ? stepNodes.length : state.completedSteps.size}/${stepNodes.length}`;
        if (barElement) barElement.style.width = `${percent}%`;
        if (progressbar) progressbar.setAttribute('aria-valuenow', String(percent));
        if (completeButton) {
            completeButton.disabled = state.completed;
            completeButton.textContent = state.completed ? panel.dataset.completedLabel : markCompleteLabel;
            completeButton.classList.toggle('opacity-60', state.completed);
            completeButton.classList.toggle('cursor-not-allowed', state.completed);
        }
    };

    const persist = async (percent, completed = false) => {
        if (state.inFlight) {
            const queued = state.pending;
            if (!queued || completed || percent > queued.percent) {
                state.pending = { percent, completed };
            }
            return state.inFlight;
        }
        if (!completed && percent <= state.lastPersisted) return true;
        if (statusElement) statusElement.textContent = panel.dataset.savingLabel;
        state.inFlight = fetch(ECuzdanEndpoints.education.progressUpdate, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken,
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ topic, phase, progress_percent: percent, completed }),
        }).then(async response => {
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) throw new Error(data.error || panel.dataset.errorLabel);
            state.lastPersisted = Math.max(state.lastPersisted, data.progress.progress_percent || 0);
            state.progressPercent = Math.max(state.progressPercent, data.progress.progress_percent || 0);
            state.completed = Boolean(data.progress.completed);
            if (statusElement) statusElement.textContent = state.completed ? panel.dataset.completedLabel : panel.dataset.savedLabel;
            render();
            return true;
        }).catch(error => {
            if (statusElement) statusElement.textContent = panel.dataset.errorLabel;
            console.error('Konu ilerlemesi kaydedilemedi:', error);
            return false;
        }).finally(() => {
            state.inFlight = null;
            const next = state.pending;
            state.pending = null;
            if (next && (next.completed || next.percent > state.lastPersisted)) {
                persist(next.percent, next.completed);
            }
        });
        return state.inFlight;
    };

    try {
        const response = await fetch(ECuzdanEndpoints.education.progress);
        const data = await response.json();
        const record = (data.progress || []).find(item => item.topic === topic);
        if (record) {
            state.progressPercent = Number(record.progress_percent) || 0;
            state.completed = Boolean(record.completed);
            state.lastPersisted = state.progressPercent;
        }
    } catch (error) {
        console.error('Konu ilerlemesi yüklenemedi:', error);
    }
    render();

    if (!state.completed && state.progressPercent === 0) await persist(5, false);

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (!entry.isIntersecting || state.completed) return;
                state.completedSteps.add(entry.target.dataset.progressStep);
                const percent = Math.round((state.completedSteps.size / stepNodes.length) * 100);
                state.progressPercent = Math.max(state.progressPercent, percent);
                render();
                persist(percent, percent >= 100);
            });
        }, { threshold: 0.55 });
        stepNodes.forEach(node => observer.observe(node));
    }

    completeButton?.addEventListener('click', () => {
        state.completed = true;
        state.progressPercent = 100;
        render();
        persist(100, true);
    });
}

// Load achievements
async function loadAchievements() {
    try {
        const response = await fetch(ECuzdanEndpoints.education.achievements);
        const data = await response.json();
        
        if (data.success) {
            updateAchievementsUI(data.achievements);
        }
    } catch (error) {
        console.error('Başarilar yükleme hatası:', error);
    }
}

function updateAchievementsUI(achievements) {
    const achievementTypes = (achievements || []).map(a => a.achievement_type);
    
    // Update achievement count
    const achievementCountElement = document.querySelector('.achievement-count');
    if (achievementCountElement) {
        achievementCountElement.textContent = (achievements || []).length;
    }
    
    // Update achievement badges
    document.querySelectorAll('.achievement-badge').forEach(badge => {
        const type = badge.dataset.type;
        if (achievementTypes.includes(type)) {
            badge.classList.remove('opacity-50');
            badge.classList.add('opacity-100');
        } else {
            badge.classList.remove('opacity-100');
            badge.classList.add('opacity-50');
        }
    });
}

// Initialize on page load if on progress view
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.search.includes('view=progress')) {
        loadProgress();
        loadAchievements();
    }
    if (document.querySelector('[data-topic-progress]')) {
        loadTopicProgress();
    }
});
