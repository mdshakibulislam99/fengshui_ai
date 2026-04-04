const cameraDirections = ['north', 'south', 'east', 'west', 'floor'];

let uploadedPhotos = {
    north: null,
    south: null,
    east: null,
    west: null,
    floor: null
};

let roomCameraStream = null;
let currentDirectionIndex = 0;

function toTitleCase(value) {
    return value ? value.charAt(0).toUpperCase() + value.slice(1) : '';
}

function getCurrentDirection() {
    return cameraDirections[currentDirectionIndex] || 'north';
}

function setCameraStatus(message) {
    const statusEl = document.getElementById('cameraStatusText');
    if (statusEl) statusEl.textContent = message;
}

function updateDirectionUI() {
    const currentDirection = getCurrentDirection();
    const currentLabel = document.getElementById('cameraCurrentDirection');
    if (currentLabel) currentLabel.textContent = toTitleCase(currentDirection);

    cameraDirections.forEach((direction) => {
        const chip = document.getElementById(`dirChip${toTitleCase(direction)}`);
        if (!chip) return;
        chip.classList.toggle('active', direction === currentDirection);
        chip.classList.toggle('captured', !!uploadedPhotos[direction]);
    });
}

function selectCameraDirection(direction) {
    const index = cameraDirections.indexOf(direction);
    if (index >= 0) {
        currentDirectionIndex = index;
        updateDirectionUI();
        setCameraStatus(`Ready to capture ${toTitleCase(direction)}.`);
    }
}

function updateCaptureButtons() {
    const hasCamera = !!roomCameraStream;
    const startBtn = document.getElementById('startCameraBtn');
    const stopBtn = document.getElementById('stopCameraBtn');
    const captureBtn = document.getElementById('captureDirectionBtn');
    const retakeBtn = document.getElementById('retakeDirectionBtn');

    if (startBtn) startBtn.disabled = hasCamera;
    if (stopBtn) stopBtn.disabled = !hasCamera;
    if (captureBtn) captureBtn.disabled = !hasCamera;
    if (retakeBtn) retakeBtn.disabled = !hasCamera;
}

function updatePreview(direction, dataUrl) {
    const title = toTitleCase(direction);
    const preview = document.getElementById(`preview${title}`);
    const label = document.getElementById(`label${title}`);

    if (preview) {
        preview.innerHTML = `<img src="${dataUrl}" alt="${direction} view">`;
        preview.style.display = 'block';
    }

    if (label) {
        label.textContent = 'Captured';
        label.style.background = '#10b981';
        label.style.color = '#fff';
    }
}

function resetPreview(direction) {
    const title = toTitleCase(direction);
    const preview = document.getElementById(`preview${title}`);
    const label = document.getElementById(`label${title}`);

    if (preview) {
        preview.innerHTML = '';
        preview.style.display = 'none';
    }

    if (label) {
        label.textContent = 'Not Captured';
        label.style.background = '';
        label.style.color = '';
    }
}

function getCapturedCount() {
    return Object.values(uploadedPhotos).filter(Boolean).length;
}

function updateAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyzeCameraBtn');
    if (analyzeBtn) {
        analyzeBtn.disabled = getCapturedCount() < 3;
    }
}

function getFirstMissingDirection() {
    return cameraDirections.find((direction) => !uploadedPhotos[direction]) || null;
}

function suggestNextDirection() {
    const missing = getFirstMissingDirection();
    if (missing) {
        selectCameraDirection(missing);
        setCameraStatus(`${toTitleCase(missing)} is next.`);
    } else {
        setCameraStatus('All 5 directions captured. Ready for best accuracy analysis.');
    }
}

function estimateSharpness(ctx, width, height) {
    const sw = Math.max(120, Math.floor(width / 5));
    const sh = Math.max(90, Math.floor(height / 5));
    const data = ctx.getImageData(0, 0, sw, sh).data;

    let gradient = 0;
    let count = 0;

    for (let y = 1; y < sh; y++) {
        for (let x = 1; x < sw; x++) {
            const i = (y * sw + x) * 4;
            const l = (y * sw + (x - 1)) * 4;
            const u = ((y - 1) * sw + x) * 4;

            const g = (data[i] + data[i + 1] + data[i + 2]) / 3;
            const gl = (data[l] + data[l + 1] + data[l + 2]) / 3;
            const gu = (data[u] + data[u + 1] + data[u + 2]) / 3;

            gradient += Math.abs(g - gl) + Math.abs(g - gu);
            count += 1;
        }
    }

    return count ? gradient / count : 0;
}

async function startRoomCamera() {
    const previewEl = document.getElementById('roomCameraPreview');
    if (!previewEl) return;

    try {
        roomCameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: 'environment' },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        });

        previewEl.srcObject = roomCameraStream;
        updateCaptureButtons();
        suggestNextDirection();
    } catch (error) {
        console.error(error);
        alert('Camera access failed. Please allow permission and try again.');
    }
}

function stopRoomCamera() {
    if (roomCameraStream) {
        roomCameraStream.getTracks().forEach((track) => track.stop());
        roomCameraStream = null;
    }

    const previewEl = document.getElementById('roomCameraPreview');
    if (previewEl) previewEl.srcObject = null;

    updateCaptureButtons();
    setCameraStatus('Camera stopped.');
}

async function captureCurrentDirection() {
    const previewEl = document.getElementById('roomCameraPreview');
    if (!previewEl || !roomCameraStream) {
        alert('Start camera first.');
        return;
    }

    if (previewEl.readyState < 2) {
        alert('Camera still loading. Please wait a second.');
        return;
    }

    const direction = getCurrentDirection();
    const canvas = document.createElement('canvas');
    canvas.width = previewEl.videoWidth || 1280;
    canvas.height = previewEl.videoHeight || 720;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(previewEl, 0, 0, canvas.width, canvas.height);

    const sharpness = estimateSharpness(ctx, canvas.width, canvas.height);
    if (sharpness < 12) {
        const ok = confirm(`The ${toTitleCase(direction)} image may be blurry. Use it anyway?`);
        if (!ok) {
            setCameraStatus(`Retake ${toTitleCase(direction)} with less motion.`);
            return;
        }
    }

    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    uploadedPhotos[direction] = dataUrl;
    updatePreview(direction, dataUrl);
    updateDirectionUI();
    updateAnalyzeButton();

    const next = getFirstMissingDirection();
    if (next) {
        selectCameraDirection(next);
        setCameraStatus(`${toTitleCase(direction)} captured. Next: ${toTitleCase(next)}.`);
    } else {
        setCameraStatus('All directions captured. Analyze now.');
    }
}

function retakeCurrentDirection() {
    const direction = getCurrentDirection();
    uploadedPhotos[direction] = null;
    resetPreview(direction);
    updateDirectionUI();
    updateAnalyzeButton();
    setCameraStatus(`${toTitleCase(direction)} reset. Capture again.`);
}

const SCORE_GRADES_INDOOR = [
    { min: 0, description: 'Poor', color: '#eab308' },
    { min: 50, description: 'Weak', color: '#eab308' },
    { min: 60, description: 'Moderate', color: '#f59e0b' },
    { min: 70, description: 'Good', color: '#10b981' },
    { min: 80, description: 'Very Good', color: '#10b981' },
    { min: 90, description: 'Excellent', color: '#059669' }
];

function escapeHtml(text) {
    return String(text || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function formatScoreLabel(key) {
    return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function getGradeForScoreIndoor(score) {
    const numericScore = Number(score);
    const safeScore = Number.isFinite(numericScore) ? numericScore : 0;

    for (let i = SCORE_GRADES_INDOOR.length - 1; i >= 0; i--) {
        if (safeScore >= SCORE_GRADES_INDOOR[i].min) {
            return SCORE_GRADES_INDOOR[i];
        }
    }

    return SCORE_GRADES_INDOOR[0];
}

function getStatusColorIndoor(score) {
    return getGradeForScoreIndoor(score).color;
}

function getScoreHealthLabelIndoor(score) {
    return getGradeForScoreIndoor(score).description;
}

function renderRadarChart(canvasId, fiveElements) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;

    const ctx = canvas.getContext('2d');
    if (canvas.chart) {
        canvas.chart.destroy();
    }

    const labels = ['Wood', 'Fire', 'Earth', 'Metal', 'Water'];
    const data = [
        fiveElements.wood || 0,
        fiveElements.fire || 0,
        fiveElements.earth || 0,
        fiveElements.metal || 0,
        fiveElements.water || 0
    ];

    canvas.chart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: 'rgba(95, 125, 106, 0.2)',
                borderColor: '#1F3D2B',
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: '#1F3D2B'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { display: false, stepSize: 20 },
                    grid: { color: '#d7e1db' },
                    angleLines: { color: '#d7e1db' },
                    pointLabels: {
                        color: '#42564b',
                        font: { size: 12 }
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label(context) {
                            return `${context.label}: ${Math.round(context.parsed.r)}`;
                        }
                    }
                }
            }
        }
    });
}

function summarizeCameraFactorsForChatbot(factors) {
    const sorted = Array.isArray(factors) ? [...factors].sort((a, b) => Number(a.score || 0) - Number(b.score || 0)) : [];
    const issues = sorted
        .filter((item) => Number(item.score || 0) < 65)
        .slice(0, 3)
        .map((item) => item.title)
        .join('; ') || 'No critical indoor issue detected';

    const strengths = sorted
        .slice()
        .reverse()
        .filter((item) => Number(item.score || 0) >= 70)
        .slice(0, 3)
        .map((item) => item.title)
        .join('; ') || 'Indoor conditions are moderate';

    return { issues, strengths };
}

function buildCameraChatbotData(analysis, factors, fiveElements, scoreMap) {
    const summary = summarizeCameraFactorsForChatbot(factors);
    const capturedDirections = cameraDirections.filter((direction) => !!uploadedPhotos[direction]);

    return {
        analysis_type: 'indoor_camera_capture',
        location: {
            address: 'Indoor guided camera analysis',
            room_type: analysis.meta?.roomType || 'general'
        },
        scores: {
            overall: Number(scoreMap.overall || 0),
            lighting: Number(scoreMap.lighting || 0),
            space_flow: Number(scoreMap.space_flow || 0),
            color_harmony: Number(scoreMap.color_harmony || 0),
            furniture_placement: Number(scoreMap.furniture_placement || 0),
            declutter: Number(scoreMap.declutter || 0),
            wood: Number(fiveElements.wood || 0),
            fire: Number(fiveElements.fire || 0),
            earth: Number(fiveElements.earth || 0),
            metal: Number(fiveElements.metal || 0),
            water: Number(fiveElements.water || 0)
        },
        issues: summary.issues,
        strengths: summary.strengths,
        features: {
            source: 'camera_guided',
            photos_analyzed: Number(analysis.meta?.photosAnalyzed || getCapturedCount()),
            captured_directions: capturedDirections,
            recommendations: Array.isArray(analysis.recommendations) ? analysis.recommendations.slice(0, 8) : [],
            factors: factors.map((f) => ({ title: f.title, score: Math.round(Number(f.score || 0)) }))
        }
    };
}

function publishCameraChatbotData(chatbotData) {
    if (!chatbotData) return;

    window.latestIndoorChatbotData = chatbotData;

    const applyData = () => {
        if (window.fengShuiChatbot && typeof window.fengShuiChatbot.setAnalysisData === 'function') {
            window.fengShuiChatbot.setAnalysisData(chatbotData);
            return true;
        }
        return false;
    };

    if (applyData()) return;

    let retries = 0;
    const maxRetries = 20;
    const retryTimer = setInterval(() => {
        retries += 1;
        if (applyData() || retries >= maxRetries) {
            clearInterval(retryTimer);
        }
    }, 200);
}

function displayCameraResults(analysis) {
    const resultsSection = document.getElementById('cameraResultsSection');
    if (!resultsSection) return;

    resultsSection.style.display = 'block';

    const categories = analysis.categories || {};
    const scoreMap = {
        overall: Number(analysis.overallScore || 0),
        lighting: Number(categories.lighting || 0),
        space_flow: Number(categories.spaceFlow || 0),
        color_harmony: Number(categories.colorHarmony || 0),
        furniture_placement: Number(categories.furniture || 0),
        declutter: Number(categories.declutter || 0)
    };

    const factors = [
        {
            title: 'Lighting & Natural Energy',
            score: scoreMap.lighting,
            confidence: 'Medium',
            dataSources: ['Camera Capture Analysis', 'Interior Lighting Heuristics'],
            mainIssue: 'Natural and artificial lighting quality influences vitality and mood in the room.',
            current: scoreMap.lighting >= 75 ? ['Natural lighting appears supportive for daily activity'] : ['Lighting appears uneven in some areas'],
            improve: scoreMap.lighting >= 75 ? ['Keep primary activity zones well lit through the day'] : ['Increase daylight access and add layered warm lighting']
        },
        {
            title: 'Space Flow & Circulation',
            score: scoreMap.space_flow,
            confidence: 'Medium',
            dataSources: ['Camera Capture Analysis', 'Qi Flow Principles'],
            mainIssue: 'Circulation routes should remain open to maintain healthy qi movement.',
            current: scoreMap.space_flow >= 70 ? ['General circulation appears reasonably open'] : ['Some movement paths look blocked or narrow'],
            improve: scoreMap.space_flow >= 70 ? ['Maintain open pathways between entry and key zones'] : ['Clear obstacles from primary paths and reduce crowding']
        },
        {
            title: 'Color Harmony',
            score: scoreMap.color_harmony,
            confidence: 'Medium',
            dataSources: ['Camera Capture Analysis', 'Five Elements Color Mapping'],
            mainIssue: 'Color and material balance affects emotional comfort and element harmony.',
            current: scoreMap.color_harmony >= 68 ? ['Color tones appear relatively balanced'] : ['Color balance appears inconsistent across areas'],
            improve: scoreMap.color_harmony >= 68 ? ['Preserve element balance when adding new decor'] : ['Add grounding earth/wood tones to balance dominant colors']
        },
        {
            title: 'Furniture Placement',
            score: scoreMap.furniture_placement,
            confidence: 'Medium',
            dataSources: ['Camera Capture Analysis', 'Command Position Rules'],
            mainIssue: 'Major furniture should support command view and avoid blocking energy flow.',
            current: scoreMap.furniture_placement >= 70 ? ['Main furniture placement appears mostly functional'] : ['Some key furniture appears suboptimal in position'],
            improve: scoreMap.furniture_placement >= 70 ? ['Keep anchor furniture aligned with room entry visibility'] : ['Reposition key furniture for better command and openness']
        },
        {
            title: 'Declutter & Organization',
            score: scoreMap.declutter,
            confidence: 'Medium',
            dataSources: ['Camera Capture Analysis', 'Clutter Impact Model'],
            mainIssue: 'Visual clutter can slow qi flow and reduce calmness.',
            current: scoreMap.declutter >= 65 ? ['Organization level appears adequate'] : ['Clutter may be reducing comfort and clarity'],
            improve: scoreMap.declutter >= 65 ? ['Maintain simple storage and visible order'] : ['Remove non-essential items and improve closed storage use']
        }
    ];

    const analysisCards = document.getElementById('cameraAnalysisCards');
    if (analysisCards) {
        analysisCards.innerHTML = `
            <div class="insights-header">
                <h3>Feng Shui AI Insights</h3>
                <p>Model-guided interpretation of camera-captured indoor factors, including score evidence and prioritized correction points.</p>
                <div class="insight-score-pill" style="display:inline-flex; margin-top:8px; background:${getStatusColorIndoor(scoreMap.overall)}1a; border-color:${getStatusColorIndoor(scoreMap.overall)}55; color:${getStatusColorIndoor(scoreMap.overall)};">
                    Overall Feng Shui: ${Math.round(scoreMap.overall)} • ${getScoreHealthLabelIndoor(scoreMap.overall)}
                </div>
            </div>
            <div class="insights-topic-grid">
                ${factors.map((factor, index) => {
                    const scoreRounded = Math.round(factor.score);
                    return `
                        <article class="insight-topic-card">
                            <div class="insight-topic-head">
                                <div class="insight-topic-title-wrap">
                                    <span class="insight-index">${index + 1}</span>
                                    <h4>${escapeHtml(factor.title)}</h4>
                                </div>
                                <div class="insight-score-pill" style="background:${getStatusColorIndoor(scoreRounded)}1a; border-color:${getStatusColorIndoor(scoreRounded)}55; color:${getStatusColorIndoor(scoreRounded)};">
                                    ${scoreRounded} • ${getScoreHealthLabelIndoor(scoreRounded)}
                                </div>
                            </div>
                            <div class="insight-block">
                                <p class="insight-meta"><strong>Confidence:</strong> ${escapeHtml(factor.confidence || 'Medium')}</p>
                                ${factor.dataSources && factor.dataSources.length ? `<p class="insight-meta"><strong>Data sources:</strong> ${factor.dataSources.map(s => escapeHtml(s)).join(' • ')}</p>` : ''}
                                ${factor.mainIssue ? `<p class="insight-meta">${escapeHtml(factor.mainIssue)}</p>` : ''}
                            </div>
                            ${factor.current && factor.current.length ? `
                                <div class="insight-block">
                                    <h5>What Is Already Good</h5>
                                    <p>${factor.current.map(item => escapeHtml(item)).join(', ')}</p>
                                </div>
                            ` : ''}
                            ${factor.improve && factor.improve.length ? `
                                <div class="insight-block">
                                    <h5>What Needs Improvement</h5>
                                    <p>${factor.improve.map(item => escapeHtml(item)).join(', ')}</p>
                                </div>
                            ` : ''}
                        </article>
                    `;
                }).join('')}
            </div>
        `;
    }

    const dashboard = document.getElementById('cameraDashboard');
    if (dashboard) {
        const scoreEntries = Object.entries(scoreMap).filter(([key]) => key !== 'overall');
        dashboard.innerHTML = `
            <div class="card">
                <h3 class="section-heading">Category Breakdown</h3>
                <div class="scores-grid">
                    ${scoreEntries.map(([key, value]) => `
                        <div class="score-card">
                            <span class="value">${Math.round(value)}</span>
                            <div class="score-indicator" style="background: ${getStatusColorIndoor(value)};"></div>
                            <span class="label">${formatScoreLabel(key)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="card" style="margin-top: 12px;">
                <div style="display:flex; align-items:center; justify-content:space-between; gap: 12px;">
                    <h3 class="section-heading" style="margin:0;">Overall Feng Shui Score</h3>
                    <span class="insight-score-pill" style="background:${getStatusColorIndoor(scoreMap.overall)}1a; border-color:${getStatusColorIndoor(scoreMap.overall)}55; color:${getStatusColorIndoor(scoreMap.overall)};">
                        ${Math.round(scoreMap.overall)} • ${getScoreHealthLabelIndoor(scoreMap.overall)}
                    </span>
                </div>
            </div>
        `;
    }

    const fiveElements = {
        wood: Math.round((scoreMap.color_harmony + scoreMap.space_flow) / 2),
        fire: Math.round((scoreMap.lighting + scoreMap.furniture_placement) / 2),
        earth: Math.round((scoreMap.declutter + scoreMap.space_flow) / 2),
        metal: Math.round((scoreMap.declutter + scoreMap.color_harmony) / 2),
        water: Math.round((scoreMap.space_flow + scoreMap.lighting) / 2)
    };

    publishCameraChatbotData(buildCameraChatbotData(analysis, factors, fiveElements, scoreMap));

    renderRadarChart('cameraElementsRadarChart', fiveElements);

    const elementAnalysis = document.getElementById('cameraElementAnalysis');
    if (elementAnalysis) {
        elementAnalysis.innerHTML = `
            <div class="scores-grid element-scores-grid">
                ${Object.entries(fiveElements).map(([element, value]) => `
                    <div class="score-card">
                        <span class="value">${Math.round(value)}</span>
                        <span class="score-indicator" style="background: ${getStatusColorIndoor(value)};"></span>
                        <span class="label" style="text-transform: capitalize;">${element}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    const recommendations = document.getElementById('cameraRecommendations');
    if (recommendations && Array.isArray(analysis.recommendations)) {
        recommendations.innerHTML = analysis.recommendations.map(rec => `
            <div class="recommendation-item" style="display:flex; gap:10px; padding:10px 12px; background:#f8fbf9; border-radius:10px; margin-bottom:10px;">
                <span>💡</span>
                <p style="margin:0; color: var(--ei-text);">${escapeHtml(rec)}</p>
            </div>
        `).join('');
    }

    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

function openCameraGuideModal() {
    const modal = document.getElementById('cameraGuideModal');
    if (modal) modal.style.display = 'flex';
}

function closeCameraGuideModal() {
    const modal = document.getElementById('cameraGuideModal');
    if (modal) modal.style.display = 'none';
}

function setupCameraGuideModalInteractions() {
    const modal = document.getElementById('cameraGuideModal');
    if (!modal) return;

    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeCameraGuideModal();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.style.display === 'flex') {
            closeCameraGuideModal();
        }
    });
}

async function analyzeCameraCapture() {
    const capturedCount = getCapturedCount();
    if (capturedCount < 3) {
        alert('Capture at least 3 directions first.');
        return;
    }

    if (capturedCount < 5) {
        const proceed = confirm('Highest accuracy needs all 5 directions. Continue anyway?');
        if (!proceed) return;
    }

    const analyzeBtn = document.getElementById('analyzeCameraBtn');
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
    }

    try {
        const response = await fetch('https://fengshui-ai.onrender.com/api/indoor-photo-analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                roomType: 'general',
                source: 'camera_guided',
                photos: uploadedPhotos
            })
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Camera analysis failed');
        }

        const data = result.data || {};
        displayCameraResults(data);
    } catch (error) {
        console.error(error);
        alert(error.message || 'Analysis failed.');
    } finally {
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Camera Capture';
        }
    }
}

window.startRoomCamera = startRoomCamera;
window.stopRoomCamera = stopRoomCamera;
window.captureCurrentDirection = captureCurrentDirection;
window.retakeCurrentDirection = retakeCurrentDirection;
window.selectCameraDirection = selectCameraDirection;
window.analyzeCameraCapture = analyzeCameraCapture;
window.openCameraGuideModal = openCameraGuideModal;
window.closeCameraGuideModal = closeCameraGuideModal;

document.addEventListener('DOMContentLoaded', () => {
    updateDirectionUI();
    updateCaptureButtons();
    updateAnalyzeButton();
    setCameraStatus('Camera is not started.');
    setupCameraGuideModalInteractions();
});