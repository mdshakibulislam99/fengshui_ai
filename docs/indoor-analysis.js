/**
 * Indoor Feng Shui Analysis System
 * Supports 3D Design Mode and Photo Upload Mode
 */

// Global state
let currentMode = null;
let placedElements = [];
let uploadedPhotos = {
    north: null,
    south: null,
    east: null,
    west: null,
    floor: null
};
let roomCameraStream = null;
let roomMediaRecorder = null;
let roomRecordedChunks = [];
let roomRecordedBlob = null;
let roomRecordedPreviewUrl = null;
const cameraDirections = ['north', 'south', 'east', 'west', 'floor'];
const cameraCapturedDirections = new Set();
let currentCameraDirectionIndex = 0;

// Three.js 3D System
let threeScene = null;
let objectLoader = null;
let interactionManager = null;
let hasUnsavedChanges = false;
let currentEditingDesignId = null;
let currentEditingDesignName = null;

// Element data for feng shui analysis
const elementFengShuiData = {
    // Furniture
    bed: { element: 'earth', energy: 'yin', placement: 'important', bagua: 'relationship' },
    sofa: { element: 'earth', energy: 'yin', placement: 'center', bagua: 'family' },
    desk: { element: 'wood', energy: 'yang', placement: 'power', bagua: 'career' },
    table: { element: 'wood', energy: 'neutral', placement: 'center', bagua: 'health' },
    chair: { element: 'wood', energy: 'yang', placement: 'supportive', bagua: 'support' },
    wardrobe: { element: 'wood', energy: 'yin', placement: 'storage', bagua: 'wealth' },
    bookshelf: { element: 'wood', energy: 'yang', placement: 'knowledge', bagua: 'knowledge' },
    tv: { element: 'fire', energy: 'yang', placement: 'entertainment', bagua: 'fame' },
    
    // Decor
    mirror: { element: 'water', energy: 'yang', placement: 'reflective', bagua: 'expansion' },
    painting: { element: 'fire', energy: 'yang', placement: 'inspiration', bagua: 'creativity' },
    clock: { element: 'metal', energy: 'yang', placement: 'time', bagua: 'helpful' },
    vase: { element: 'earth', energy: 'yin', placement: 'decorative', bagua: 'peace' },
    rug: { element: 'earth', energy: 'yin', placement: 'grounding', bagua: 'stability' },
    curtain: { element: 'water', energy: 'yin', placement: 'privacy', bagua: 'protection' },
    window: { element: 'metal', energy: 'yang', placement: 'openness', bagua: 'opportunities' },
    door: { element: 'wood', energy: 'yang', placement: 'entry', bagua: 'career' },
    fountain: { element: 'water', energy: 'yang', placement: 'flow', bagua: 'wealth' },
    crystals: { element: 'earth', energy: 'yang', placement: 'energy', bagua: 'clarity' },
    
    // Plants
    bamboo: { element: 'wood', energy: 'yang', placement: 'growth', bagua: 'prosperity' },
    plant: { element: 'wood', energy: 'yang', placement: 'life', bagua: 'health' },
    bonsai: { element: 'wood', energy: 'yin', placement: 'balance', bagua: 'wisdom' },
    flowers: { element: 'wood', energy: 'yang', placement: 'beauty', bagua: 'love' },
    
    // Lighting
    lamp: { element: 'fire', energy: 'yang', placement: 'illumination', bagua: 'clarity' },
    chandelier: { element: 'fire', energy: 'yang', placement: 'grandeur', bagua: 'wealth' },
    candle: { element: 'fire', energy: 'yang', placement: 'warmth', bagua: 'passion' }
};

// ==================== MODE SELECTION ====================
function selectMode(mode) {
    currentMode = mode;
    
    // Save the selected mode to localStorage for page refresh persistence
    localStorage.setItem('currentMode', mode);
    
    // Push state to browser history for back button support
    history.pushState({ mode: mode }, '', '');
    
    const modeSelection = document.getElementById('modeSelection');
    const designMode = document.getElementById('designMode');
    const uploadMode = document.getElementById('uploadMode');

    if (modeSelection) {
        modeSelection.classList.remove('active');
    }
    
    if (mode === 'design' && designMode) {
        designMode.classList.add('active');
        // Wait for DOM to update and container to have dimensions
        setTimeout(() => {
            const container = document.getElementById('roomCanvas');
            if (container) {
                console.log('Container found, dimensions:', container.clientWidth, 'x', container.clientHeight);
            }
            initialize3DScene();
        }, 150);
    } else if (mode === 'upload' && uploadMode) {
        uploadMode.classList.add('active');
    }
}

function backToSelection() {
    // Check if there's unsaved work
    if (placedElements.length > 0 && hasUnsavedChanges) {
        customConfirm(
            'You have unsaved changes. Going back will discard them. Continue?',
            'Leave Design Mode?'
        ).then(confirmed => {
            if (confirmed) {
                performBackToSelection();
            }
        });
        return;
    }
    performBackToSelection();
}

function performBackToSelection() {
    currentMode = null;
    currentEditingDesignId = null;
    currentEditingDesignName = null;
    hasUnsavedChanges = false;
    
    // Clear the mode from localStorage when going back to selection
    localStorage.removeItem('currentMode');
    
    const modeSelection = document.getElementById('modeSelection');
    const designMode = document.getElementById('designMode');
    const uploadMode = document.getElementById('uploadMode');

    if (modeSelection) modeSelection.classList.add('active');
    if (designMode) designMode.classList.remove('active');
    if (uploadMode) uploadMode.classList.remove('active');
    
    // Reset states without confirmation (already confirmed)
    if (interactionManager) {
        interactionManager.clearAll();
    }
    placedElements = [];
    updatePlacedItemsList();
    updateItemCount();
    
    resetUpload();
    
    // Dispose 3D scene
    if (threeScene) {
        threeScene.dispose();
        threeScene = null;
    }
    if (interactionManager) {
        interactionManager.dispose();
        interactionManager = null;
    }
    
    // Update history state to selection mode
    history.pushState({ mode: 'selection' }, '', '');
}

// ==================== 3D SCENE INITIALIZATION ====================

function initialize3DScene() {
    try {
        console.log('Starting 3D scene initialization...');
        
        const container = document.getElementById('roomCanvas');
        const loading = document.getElementById('canvasLoading');
        
        // Validate container
        if (!container) {
            throw new Error('Room canvas container not found');
        }
        
        // Check container dimensions
        const rect = container.getBoundingClientRect();
        console.log('Container dimensions:', rect.width, 'x', rect.height);
        
        if (rect.width === 0 || rect.height === 0) {
            throw new Error('Container has zero dimensions. Please ensure the design mode is visible.');
        }
        
        // Check if Three.js is loaded
        if (typeof THREE === 'undefined') {
            throw new Error('Three.js library not loaded. Check your internet connection.');
        }
        console.log('✓ Three.js loaded, version:', THREE.REVISION);
        
        // Check WebGL support
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (!gl) {
            throw new Error('WebGL is not supported in your browser. Please use Chrome, Firefox, or Edge.');
        }
        console.log('✓ WebGL supported');
        
        // Initialize scene (OrbitControls will be checked in ThreeScene)
        console.log('Creating ThreeScene...');
        if (typeof ThreeScene === 'undefined') {
            throw new Error('ThreeScene module not loaded. Check threeScene.js file.');
        }
        if (typeof ObjectLoader === 'undefined') {
            throw new Error('ObjectLoader module not loaded. Check objectLoader.js file.');
        }
        if (typeof InteractionManager === 'undefined') {
            throw new Error('InteractionManager module not loaded. Check interaction.js file.');
        }
        console.log('✓ All custom modules loaded');
        
        // Initialize scene
        console.log('Creating ThreeScene...');
        threeScene = new ThreeScene('roomCanvas');
        
        console.log('Creating ObjectLoader...');
        objectLoader = new ObjectLoader(threeScene);
        
        console.log('Creating InteractionManager...');
        interactionManager = new InteractionManager(threeScene, objectLoader);
        
        // Hide loading indicator
        if (loading) {
            loading.style.display = 'none';
        }
        
        console.log('✅ 3D Scene initialized successfully!');
        
        // Setup event listeners for 3D system
        setup3DEventListeners();
        
        // Check for unsaved work from previous session
        checkForUnsavedWork();
        
        // Add beforeunload warning
        window.addEventListener('beforeunload', handleBeforeUnload);
        
    } catch (error) {
        console.error('❌ Failed to initialize 3D scene:', error);
        console.error('Error details:', error.message);
        console.error('Error stack:', error.stack);
        
        // Hide loading indicator
        const loading = document.getElementById('canvasLoading');
        if (loading) {
            loading.innerHTML = `
                <div style="text-align: center; color: #ef4444;">
                    <p style="font-size: 20px; margin-bottom: 10px;">⚠️ 3D Initialization Failed</p>
                    <p style="font-size: 14px; margin-bottom: 15px;">${error.message}</p>
                    <button onclick="location.reload()" style="padding: 10px 20px; background: #00A99D; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                        Reload Page
                    </button>
                </div>
            `;
        }
    }
}

function setup3DEventListeners() {
    // Object placed
    document.addEventListener('objectPlaced', () => {
        syncPlacedElementsFromScene();
        if (!interactionManager?.selectedObject) {
            clearElementDetails();
        }
        markAsUnsaved(); // Mark as modified
    });
    
    // Object moved
    document.addEventListener('objectMoved', () => {
        syncPlacedElementsFromScene();
        markAsUnsaved(); // Mark as modified
    });
    
    // Object rotated
    document.addEventListener('objectRotated', (event) => {
        markAsUnsaved(); // Mark as modified
    });
    
    // Object selected
    document.addEventListener('objectSelected', (event) => {
        showElementDetails(event.detail);
    });
    
    // Object deselected
    document.addEventListener('objectDeselected', () => {
        clearElementDetails();
    });
    
    // Object deleted
    document.addEventListener('objectDeleted', () => {
        syncPlacedElementsFromScene();
        if (!interactionManager?.selectedObject) {
            clearElementDetails();
        }
        markAsUnsaved(); // Mark as modified
    });
    
    // All objects cleared
    document.addEventListener('allObjectsCleared', () => {
        syncPlacedElementsFromScene();
        clearElementDetails();
        hasUnsavedChanges = false;
    });
    
    // Auto-save temp design every 30 seconds
    setInterval(() => {
        if (hasUnsavedChanges && placedElements.length > 0) {
            saveTempDesign();
        }
    }, 30000);
}

function syncPlacedElementsFromScene() {
    if (!interactionManager || typeof interactionManager.getPlacedObjects !== 'function') {
        return;
    }

    // Keep source of truth from actual scene objects to avoid duplicate UI entries.
    placedElements = interactionManager.getPlacedObjects().map(obj => ({
        type: obj.type,
        position: obj.position,
        fengShui: obj.fengShui
    }));

    updatePlacedItemsList();
    updateItemCount();
}

// ==================== DESIGN MODE ====================

async function analyzeDesign() {
    console.log('🔍 Analyze button clicked! Elements placed:', placedElements.length);
    
    if (!placedElements.length) {
        await customAlert('Please place at least one element in the room before analyzing.', 'No Elements', 'warning');
        return;
    }
    
    const roomType = document.getElementById('roomTypeDesign')?.value || 'bedroom';
    console.log('📋 Room type:', roomType);
    
    const requestData = {
        roomType,
        elements: placedElements.map(e => ({
            type: e.type,
            position: e.position,
            fengShui: e.fengShui
        }))
    };
    
    console.log('📤 Sending request to backend:', requestData);
    
    // Show loading state on button
    const analyzeBtn = document.querySelector('.analyze-btn');
    const originalText = analyzeBtn.textContent;
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '⏳ Analyzing...';
    
    showIndoorLoading();
    
    try {
        const response = await fetch('https://fengshui-ai.onrender.com/api/indoor-analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        console.log('📥 Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ Response error:', errorText);
            throw new Error('Analysis failed: ' + response.status);
        }
        
        const data = await response.json();
        console.log('✅ Response data:', data);
        
        if (!data.success) throw new Error(data.error || 'Analysis failed');
        
        renderIndoorResults(data.data);
        
        // Reset button
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = originalText;
    } catch (error) {
        console.error('❌ Analysis error:', error);
        showIndoorError(error.message || 'Analysis failed. Please ensure backend server is running.');
        
        // Reset button
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = originalText;
    }
}

function showIndoorLoading() {
    // Keep results section hidden during loading
    const results = document.getElementById('designResults');
    results.style.display = 'none';
    
    // Optional: Show a loading indicator near the analyze button
    console.log('⏳ Analysis in progress...');
}

function showIndoorError(msg) {
    // Show error message in alert/modal instead of in results area
    customAlert(
        msg + '\n\nPlease make sure the backend server is running on port 3000.',
        'Analysis Error',
        'error'
    );
    
    console.error('❌ Analysis failed:', msg);
}

function publishIndoorChatbotData(chatbotData) {
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

    // Chatbot script may initialize slightly later on some page loads.
    let retries = 0;
    const retryTimer = setInterval(() => {
        retries += 1;
        if (applyData() || retries >= 10) {
            clearInterval(retryTimer);
        }
    }, 250);
}

function summarizeIndoorFactorsForChatbot(factors = []) {
    const strengths = [];
    const issues = [];

    factors.forEach((factor) => {
        const title = String(factor.title || 'Factor');
        const score = Number(factor.score || 0);
        if (score >= 70) {
            strengths.push(`${title} strong (${Math.round(score)}/100)`);
        } else {
            issues.push(`${title} needs improvement (${Math.round(score)}/100)`);
        }
    });

    return {
        strengths: strengths.length ? strengths.join('; ') : 'No major strengths identified yet',
        issues: issues.length ? issues.join('; ') : 'No major issues detected'
    };
}

function buildDesignChatbotData(result) {
    const roomType = document.getElementById('roomTypeDesign')?.value || 'bedroom';
    const scores = result.scores || {};
    const factors = result.factors || [];
    const summary = summarizeIndoorFactorsForChatbot(factors);

    return {
        analysis_type: 'indoor_design',
        location: {
            address: `Indoor ${roomType} design analysis`,
            room_type: roomType
        },
        scores: {
            overall: Number(scores.overall || 0),
            element_balance: Number(scores.element_balance || 0),
            energy_balance: Number(scores.energy_balance || 0),
            space_flow: Number(scores.space_flow || 0),
            functional_layout: Number(scores.functional_layout || 0),
            wood: Number(scores.wood || 0),
            fire: Number(scores.fire || 0),
            earth: Number(scores.earth || 0),
            metal: Number(scores.metal || 0),
            water: Number(scores.water || 0)
        },
        issues: summary.issues,
        strengths: summary.strengths,
        features: {
            placed_elements_count: placedElements.length,
            placed_elements: placedElements.map(item => item.type).slice(0, 30),
            factors: factors.map(f => ({ title: f.title, score: Math.round(Number(f.score || 0)) }))
        }
    };
}

function buildUploadChatbotData(analysis, factors, fiveElements) {
    const categories = analysis.categories || {};
    const summary = summarizeIndoorFactorsForChatbot(factors);

    return {
        analysis_type: 'indoor_photo_upload',
        location: {
            address: 'Indoor photo analysis',
            room_type: analysis.meta?.roomType || 'general'
        },
        scores: {
            overall: Number(analysis.overallScore || 0),
            lighting: Number(categories.lighting || 0),
            space_flow: Number(categories.spaceFlow || 0),
            color_harmony: Number(categories.colorHarmony || 0),
            furniture_placement: Number(categories.furniture || 0),
            declutter: Number(categories.declutter || 0),
            wood: Number(fiveElements.wood || 0),
            fire: Number(fiveElements.fire || 0),
            earth: Number(fiveElements.earth || 0),
            metal: Number(fiveElements.metal || 0),
            water: Number(fiveElements.water || 0)
        },
        issues: summary.issues,
        strengths: summary.strengths,
        features: {
            photos_analyzed: Number(analysis.meta?.photosAnalyzed || 0),
            recommendations: Array.isArray(analysis.recommendations) ? analysis.recommendations.slice(0, 8) : []
        }
    };
}

function renderIndoorResults(result) {
    // result: { scores, factors: [{title, score, current, missing, improve}], summary, suggestions }
    const results = document.getElementById('designResults');
    
    // Analysis Factor Cards (Left Column - using outdoor analysis structure)
    const analysisCards = document.getElementById('analysisCards');
    const factors = result.factors || [];
    
    analysisCards.innerHTML = `
        <div class="insights-header">
            <h3>Feng Shui AI Insights</h3>
            <p>Model-guided interpretation of core factors, including score evidence, strengths, and prioritized correction points.</p>
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
                            ${factor.current && factor.current.length ? `
                                <ul class="insight-mini-list">
                                    ${factor.current.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                                </ul>
                            ` : ''}
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
    
    // Scores Breakdown Grid (Right Column - matching outdoor)
    const scores = result.scores || {};
    const dashboard = document.getElementById('dashboard');
    const scoreEntries = Object.entries(scores).filter(([key]) => key !== 'overall');
    const overallScore = Number(scores.overall || 0);
    const scorePercent = Math.max(0, Math.min(100, overallScore));
    const scoreGrade = getGradeForScoreIndoor(overallScore);
    const activeColor = scoreGrade.color;
    const gaugeRadius = 80;
    const gaugeCircumference = 2 * Math.PI * gaugeRadius;
    const gaugeOffset = gaugeCircumference * (1 - scorePercent / 100);
    
    dashboard.innerHTML = `
        <div class="card" style="margin-bottom: 12px;">
            <h3 class="section-heading" style="margin-top:0;">Overall Feng Shui Score</h3>
            <div class="analysis-header">
                <div class="gauge-container">
                    <svg class="circular-gauge" viewBox="0 0 200 200">
                        <circle class="gauge-bg" cx="100" cy="100" r="80" fill="none" stroke="#e5e7eb" stroke-width="20"/>
                        <circle cx="100" cy="100" r="80" fill="none" stroke="${activeColor}" stroke-width="20" stroke-linecap="round" stroke-dasharray="${gaugeCircumference}" stroke-dashoffset="${gaugeOffset}" transform="rotate(-90 100 100)"/>
                    </svg>
                    <div class="gauge-content">
                        <div class="gauge-score">${Math.round(overallScore)}</div>
                    </div>
                </div>
                <div class="analysis-info">
                    <div class="info-label">Overall Feng Shui</div>
                    <div class="info-status"><strong>${scoreGrade.description}</strong></div>
                    <div class="color-bar">
                        <div class="color-segment" style="background-color:${activeColor}; width:100%;"></div>
                    </div>
                    <div class="score-legend" aria-label="Score color legend">
                        ${SCORE_GRADES_INDOOR.map((grade) => `
                            <span class="legend-item"><span class="legend-dot" style="background:${grade.color};"></span><span class="legend-label">${grade.description}</span></span>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
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
    `;
    
    // Five Elements Radar Chart
    const fiveElements = result.fiveElements || {
        wood: scores.wood || 0,
        fire: scores.fire || 0,
        earth: scores.earth || 0,
        metal: scores.metal || 0,
        water: scores.water || 0
    };
    renderRadarChart('elementsRadarChart', fiveElements);
    
    // Element Analysis
    const elementAnalysis = document.getElementById('elementAnalysis');
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
    
    // Show results section and scroll to it smoothly
    results.style.display = 'block';

    publishIndoorChatbotData(buildDesignChatbotData(result));

    setTimeout(() => {
        results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function renderRadarChart(canvasId, fiveElements) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if present
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
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: 'rgba(0, 169, 157, 0.2)',
                borderColor: '#00A99D',
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: '#00A99D'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        display: false,
                        stepSize: 20
                    },
                    grid: {
                        color: '#d7e1db'
                    },
                    angleLines: {
                        color: '#d7e1db'
                    },
                    pointLabels: {
                        color: '#42564b',
                        font: {
                            size: 12
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
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

function formatScoreLabel(key) {
    return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function getScoreColor(score) {
    if (score >= 80) return '#00A99D';
    if (score >= 60) return '#00A99D';
    if (score >= 40) return '#00A99D';
    if (score >= 20) return '#00A99D';
    return '#00A99D';
}

function getStatusText(score) {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Balanced';
    if (score >= 40) return 'Moderate';
    if (score >= 20) return 'Weak';
    return 'Poor';
}

function escapeHtml(text) {
    return String(text || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function AnalysisCard({ title, score, current = [], missing = [], improve = [], confidence = 'Medium', dataSources = [], mainIssue = '' }, cardNumber) {
    const numeric = Math.max(0, Math.min(100, Number(score)));
    const statusText = getScoreBadgeText(numeric);
    const badgeColor = getScoreBadgeColor(numeric);
    
    return `
        <article class="card analysis-card">
            <div class="card-header-row">
                <h4 class="card-number-title"><span class="card-number">${cardNumber}</span> ${escapeHtml(title)}</h4>
                <span class="status-badge" style="background-color: ${badgeColor};">${Math.round(numeric)} • ${statusText}</span>
            </div>
            
            <div class="card-meta">
                <p><strong>Confidence:</strong> ${escapeHtml(confidence)}</p>
                ${dataSources.length ? `<p><strong>Data sources:</strong> ${dataSources.map(s => escapeHtml(s)).join(' • ')}</p>` : ''}
                ${mainIssue ? `<p class="main-issue">${escapeHtml(mainIssue)}</p>` : ''}
            </div>
            
            ${current.length ? `
                <ul class="metric-points">
                    ${current.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>
            ` : ''}
            
            ${current.length || improve.length ? `
                <div class="card-sections">
                    ${current.length ? `
                        <div class="card-section">
                            <h5>What Is Already Good</h5>
                            <p>${current.map(item => escapeHtml(item)).join(', ')}</p>
                        </div>
                    ` : ''}
                    
                    ${improve.length ? `
                        <div class="card-section">
                            <h5>What Needs Improvement</h5>
                            <p>${improve.map(item => escapeHtml(item)).join(', ')}</p>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
        </article>
    `;
}

// Score color and label functions matching outdoor analysis
const SCORE_GRADES_INDOOR = [
    { min: 0, description: 'Poor', color: '#eab308' },
    { min: 50, description: 'Weak', color: '#eab308' },
    { min: 60, description: 'Moderate', color: '#f59e0b' },
    { min: 70, description: 'Good', color: '#00A99D' },
    { min: 80, description: 'Very Good', color: '#00A99D' },
    { min: 90, description: 'Excellent', color: '#059669' }
];

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

// ...existing code...

// Element interaction - Click or Drag to activate ghost mode
/**
 * Place element immediately when clicked (auto-place mode)
 * Flow: Click element → Auto-placed in room → Edit by dragging or double-click to reposition
 */
function selectElementToPlace(elementType) {
    if (elementType && interactionManager) {
        const fengShuiData = elementFengShuiData[elementType];
        // Directly place object at default position (no ghost mode, no drag required)
        interactionManager.placeObjectDirectly(elementType, fengShuiData);
    }
}

function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    const elementType = ev.target.getAttribute('data-element');
    ev.dataTransfer.setData("element", elementType);
}

/**
 * Handle drag-and-drop placement (also uses auto-place mode)
 */
function drop(ev) {
    ev.preventDefault();
    const elementType = ev.dataTransfer.getData("element");
    
    if (elementType && interactionManager) {
        const fengShuiData = elementFengShuiData[elementType];
        // Directly place object (no ghost mode required)
        interactionManager.placeObjectDirectly(elementType, fengShuiData);
    }
}

function getElementIcon(type) {
    const libraryItem = document.querySelector(`.element-item[data-element="${type}"]`);
    return libraryItem ? libraryItem.querySelector('.element-icon')?.textContent || '📦' : '📦';
}

function formatElementName(type) {
    return type ? type.charAt(0).toUpperCase() + type.slice(1) : 'Unknown';
}

function formatDisplayValue(value) {
    if (!value || typeof value !== 'string') return 'Unknown';
    return value
        .split(' ')
        .map(part => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
}

function showUsedElementDetails(index) {
    const item = placedElements[index];
    if (!item) return;

    const fallbackFengShui = elementFengShuiData[item.type] || {
        element: 'unknown',
        energy: 'unknown',
        bagua: 'unknown'
    };

    showElementDetails({
        type: item.type,
        position: item.position || { x: 0, z: 0 },
        rotation: 0,
        fengShui: item.fengShui || fallbackFengShui
    }, true);
}

// Show element details when selected
function showElementDetails(details, showBack = true) {
    const detailsPanel = document.getElementById('elementDetails');
    if (!detailsPanel) return;
    
    const { type, position, rotation, fengShui } = details;
    
    detailsPanel.innerHTML = `
        <div class="detail-section">
            <div class="detail-topbar">
                ${showBack ? '<button class="detail-back-btn" onclick="clearElementDetails()" title="Back to used elements">←</button>' : '<span></span>'}
                <h4>${formatElementName(type)}</h4>
            </div>
            <div class="detail-item">
                <strong>Feng Shui Element:</strong> ${formatDisplayValue(fengShui.element)}
            </div>
            <div class="detail-item">
                <strong>Energy:</strong> ${formatDisplayValue(fengShui.energy)}
            </div>
            <div class="detail-item">
                <strong>Bagua Area:</strong> ${formatDisplayValue(fengShui.bagua)}
            </div>
            <div class="detail-item">
                <strong>Position:</strong> 
                X: ${position.x.toFixed(2)}, Z: ${position.z.toFixed(2)}
            </div>
            <div class="controls-section">
                <button onclick="rotateSelected()" class="control-btn">Rotate (R)</button>
                <button onclick="deleteSelected()" class="control-btn delete-btn">Delete</button>
            </div>
            <div class="help-text">
                <p><strong>Controls:</strong></p>
                <ul>
                    <li>Click & drag to move</li>
                    <li>Press R to rotate</li>
                    <li>Press Delete to remove</li>
                    <li>Right-click + drag to rotate view</li>
                    <li>Scroll to zoom</li>
                </ul>
            </div>
        </div>
    `;
}

function clearElementDetails() {
    const detailsPanel = document.getElementById('elementDetails');
    if (!detailsPanel) return;

    if (placedElements.length === 0) {
        detailsPanel.innerHTML = `
            <div class="detail-placeholder">
                <p>No elements used yet</p>
                <p class="detail-hint">Place an element, then select it to view details</p>
            </div>
        `;
        return;
    }

    const usedList = placedElements.map((item, index) => {
        const icon = getElementIcon(item.type);
        const name = formatElementName(item.type);
        const element = item.fengShui?.element || elementFengShuiData[item.type]?.element || 'unknown';
        return `
            <button class="used-element-item" onclick="showUsedElementDetails(${index})" title="View ${name} details">
                <span class="used-element-icon">${icon}</span>
                <span class="used-element-name">${name}</span>
                <span class="used-element-tag">${element}</span>
            </button>
        `;
    }).join('');

    detailsPanel.innerHTML = `
        <div class="detail-section used-elements-section">
            <div class="detail-topbar">
                <span></span>
                <h4>Used Elements (${placedElements.length})</h4>
            </div>
            <div class="used-elements-list">
                ${usedList}
            </div>
            <div class="help-text">
                <p><strong>Tip:</strong> Click any object in the 3D room or an item above to view full details.</p>
            </div>
        </div>
    `;
}

function rotateSelected() {
    if (interactionManager) {
        interactionManager.rotateSelectedObject();
    }
}

function deleteSelected() {
    if (interactionManager) {
        interactionManager.deleteSelectedObject();
    }
}

function clearCanvas() {
    customConfirm(
        'Are you sure you want to clear all objects?',
        'Clear All Objects?'
    ).then(confirmed => {
        if (confirmed) {
            if (interactionManager) {
                interactionManager.clearAll();
            }
            placedElements = [];
            hasUnsavedChanges = false;
            currentEditingDesignId = null;
            currentEditingDesignName = null;
            updatePlacedItemsList();
            updateItemCount();
            
            const resultsDiv = document.getElementById('designResults');
            if (resultsDiv) {
                resultsDiv.style.display = 'none';
            }
            
            showToast('All objects cleared', 'info');
        }
    });
}

// ==================== AUTO-SAVE TO LOCALSTORAGE ====================

// ==================== UNSAVED CHANGES TRACKING ====================

function markAsUnsaved() {
    hasUnsavedChanges = true;
    console.log('Design marked as modified');
}

function handleBeforeUnload(event) {
    if (hasUnsavedChanges && placedElements.length > 0) {
        event.preventDefault();
        event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return event.returnValue;
    }
}

function saveTempDesign() {
    if (!interactionManager || !threeScene || placedElements.length === 0) return;
    
    try {
        const designData = {
            placedElements: placedElements,
            objects: interactionManager.getPlacedObjects(),
            roomType: document.getElementById('roomTypeDesign')?.value || 'bedroom',
            timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('fengshui_temp_design', JSON.stringify(designData));
        console.log('✓ Temporary design saved');
    } catch (error) {
        console.error('Failed to save temp design:', error);
    }
}

async function checkForUnsavedWork() {
    try {
        const tempData = localStorage.getItem('fengshui_temp_design');
        if (tempData) {
            const designData = JSON.parse(tempData);
            if (designData.objects && designData.objects.length > 0) {
                const shouldSave = await customConfirm(
                    'You have unsaved work from your previous session. Would you like to save it?',
                    'Unsaved Work Found'
                );
                
                if (shouldSave) {
                    // Restore the temp design for saving
                    restoreTempDesign(designData);
                    // Prompt to save
                    setTimeout(() => saveDesignToAccount(), 500);
                } else {
                    // Clear temp design
                    localStorage.removeItem('fengshui_temp_design');
                    console.log('Temp design cleared by user');
                }
            }
        }
    } catch (error) {
        console.error('Error checking for unsaved work:', error);
    }
}

function restoreTempDesign(designData) {
    try {
        // Restore room type
        if (designData.roomType) {
            const roomTypeSelect = document.getElementById('roomTypeDesign');
            if (roomTypeSelect) {
                roomTypeSelect.value = designData.roomType;
            }
        }
        
        // Restore objects
        if (designData.objects && designData.objects.length > 0) {
            designData.objects.forEach(obj => {
                if (objectLoader && threeScene) {
                    const object = objectLoader.loadObject(obj.type, obj.fengShui);
                    object.position.copy(obj.position);
                    object.rotation.y = obj.rotation;
                    
                    // Mark as fixed so it can be unlocked and edited
                    object.userData.isFixed = true;
                    object.userData.isGhost = false;
                    
                    threeScene.addObject(object);
                    
                    placedElements.push({
                        type: obj.type,
                        position: obj.position,
                        fengShui: obj.fengShui
                    });
                }
            });
            
            updatePlacedItemsList();
            updateItemCount();
            hasUnsavedChanges = true;
            console.log('✓ Temporary design restored');
        }
    } catch (error) {
        console.error('Failed to restore temp design:', error);
    }
}

// ==================== SAVE TO BACKEND (USER ACCOUNT) ====================

async function saveDesignToAccount() {
    console.log('Save button clicked');
    console.log('Current state:', {
        hasInteractionManager: !!interactionManager,
        hasThreeScene: !!threeScene,
        placedElementsCount: placedElements.length,
        currentMode: currentMode,
        isEditing: !!currentEditingDesignId
    });
    
    if (!interactionManager || !threeScene) {
        console.error('Save failed: 3D scene not initialized');
        await customAlert('The 3D scene is not initialized yet. Please wait a moment and try again.', 'Scene Not Ready', 'warning');
        return;
    }
    
    if (placedElements.length === 0) {
        console.warn('Save failed: No objects placed');
        await customAlert('Please place at least one object before saving.', 'No Objects Placed', 'warning');
        return;
    }
    
    let designName;
    
    // If editing existing design, ask to update or save as new
    if (currentEditingDesignId && currentEditingDesignName) {
        const shouldUpdate = await customConfirm(
            `Update existing design "${currentEditingDesignName}"? Click Cancel to save as new design.`,
            'Update Design?'
        );
        
        if (shouldUpdate) {
            designName = currentEditingDesignName;
        } else {
            designName = await customPrompt(
                'Enter a name for the new design (leave empty for auto-name):',
                'Save as New Design',
                `${currentEditingDesignName} (Copy)`
            );
            
            // If no name provided, generate auto-name
            if (!designName) {
                const savedDesigns = JSON.parse(localStorage.getItem('fengshui_saved_designs') || '[]');
                const designNumber = savedDesigns.length + 1;
                designName = `#design${designNumber}`;
                console.log('Auto-generated design name:', designName);
            }
            
            currentEditingDesignId = null; // Save as new
        }
    } else {
        designName = await customPrompt(
            'Enter a name for this design (leave empty for auto-name):',
            'Save Design',
            ''
        );
        
        // If no name provided, generate auto-name
        if (!designName) {
            const savedDesigns = JSON.parse(localStorage.getItem('fengshui_saved_designs') || '[]');
            const designNumber = savedDesigns.length + 1;
            designName = `#design${designNumber}`;
            console.log('Auto-generated design name:', designName);
        }
    }
    
    try {
        console.log('Attempting to save design:', designName);
        
        const designData = {
            name: designName,
            placedElements: placedElements,
            objects: interactionManager.getPlacedObjects(),
            roomType: document.getElementById('roomTypeDesign')?.value || 'bedroom',
            timestamp: new Date().toISOString()
        };
        
        console.log('Design data prepared:', {
            name: designData.name,
            objectsCount: designData.objects?.length || 0,
            roomType: designData.roomType
        });
        
        // For now, save to localStorage as fallback (will be replaced with backend API)
        let savedDesigns = JSON.parse(localStorage.getItem('fengshui_saved_designs') || '[]');
        
        if (currentEditingDesignId) {
            // Update existing design
            const index = savedDesigns.findIndex(d => d.id === currentEditingDesignId);
            if (index !== -1) {
                designData.id = currentEditingDesignId;
                savedDesigns[index] = designData;
                console.log('✓ Design updated successfully');
                showToast(`Design "${designName}" updated successfully!`, 'success');
            } else {
                // Design not found, save as new
                designData.id = Date.now().toString();
                savedDesigns.push(designData);
                currentEditingDesignId = designData.id;
                console.log('✓ Design saved as new (original not found)');
                showToast(`Design "${designName}" saved successfully!`, 'success');
            }
        } else {
            // Save as new design
            designData.id = Date.now().toString();
            savedDesigns.push(designData);
            currentEditingDesignId = designData.id;
            console.log('✓ Design saved successfully to localStorage');
            showToast(`Design "${designName}" saved successfully!`, 'success');
        }
        
        currentEditingDesignName = designName;
        hasUnsavedChanges = false;
        localStorage.removeItem('fengshui_temp_design'); // Clear temp design after saving
        localStorage.setItem('fengshui_saved_designs', JSON.stringify(savedDesigns));
        
        // TODO: Replace with actual backend API call
        /*
        const response = await fetch('/api/save-design', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getUserToken()}`
            },
            body: JSON.stringify(designData)
        });
        
        if (!response.ok) throw new Error('Failed to save design');
        
        const result = await response.json();
        showToast(`Design "${designName}" saved successfully!`, 'success');
        */
    } catch (error) {
        console.error('Failed to save design:', error);
        console.error('Error stack:', error.stack);
        await customAlert('Failed to save design. Please try again.', 'Save Failed', 'error');
    }
}

async function showHistoryModal() {
    const modal = document.getElementById('historyModal');
    const designsList = document.getElementById('savedDesignsList');
    
    if (!modal || !designsList) return;
    
    modal.style.display = 'flex';
    designsList.innerHTML = '<div class="loading-spinner"></div><p>Loading your saved designs...</p>';
    
    try {
        // For now, load from localStorage (will be replaced with backend API)
        const savedDesigns = JSON.parse(localStorage.getItem('fengshui_saved_designs') || '[]');
        
        // TODO: Replace with actual backend API call
        /*
        const response = await fetch('/api/get-designs', {
            headers: {
                'Authorization': `Bearer ${getUserToken()}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load designs');
        const savedDesigns = await response.json();
        */
        
        if (savedDesigns.length === 0) {
            designsList.innerHTML = `
                <div class="empty-designs">
                    <p>No saved designs yet</p>
                    <p style="font-size: 14px;">Start designing and save your first layout!</p>
                </div>
            `;
            return;
        }
        
        // Sort designs by timestamp (latest first)
        const sortedDesigns = savedDesigns.sort((a, b) => {
            return new Date(b.timestamp) - new Date(a.timestamp);
        });
        
        // Display saved designs
        designsList.innerHTML = sortedDesigns.map(design => {
            const isAutoNamed = design.name.startsWith('#design');
            const displayName = isAutoNamed 
                ? `<span style="color: #8b5cf6; font-weight: 600;">${design.name}</span>` 
                : design.name;
            
            return `
            <div class="saved-design-card" data-design-id="${design.id}">
                <div class="saved-design-header">
                    <div class="saved-design-name">${displayName}</div>
                    <div class="saved-design-date">${new Date(design.timestamp).toLocaleDateString()}</div>
                </div>
                <div class="saved-design-info">
                    <span>Room: ${design.roomType || 'bedroom'}</span>
                    <span>Objects: ${design.objects?.length || 0}</span>
                    <span>Time: ${new Date(design.timestamp).toLocaleTimeString()}</span>
                </div>
                <div class="saved-design-actions">
                    <button class="design-action-btn edit" onclick="editDesignById('${design.id}')" title="Edit this design">Edit Design</button>
                    <button class="design-action-btn delete" onclick="deleteDesignById('${design.id}')" title="Delete this design">Delete</button>
                </div>
            </div>
        `}).join('');
        
    } catch (error) {
        console.error('Failed to load saved designs:', error);
        designsList.innerHTML = `
            <div class="empty-designs">
                <p>Failed to load designs</p>
                <p style="font-size: 14px;">Please try again later</p>
            </div>
        `;
    }
}

function closeHistoryModal() {
    const modal = document.getElementById('historyModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function editDesignById(designId) {
    try {
        // For now, load from localStorage (will be replaced with backend API)
        const savedDesigns = JSON.parse(localStorage.getItem('fengshui_saved_designs') || '[]');
        const design = savedDesigns.find(d => d.id === designId);
        
        // TODO: Replace with actual backend API call
        /*
        const response = await fetch(`/api/get-design/${designId}`, {
            headers: {
                'Authorization': `Bearer ${getUserToken()}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load design');
        const design = await response.json();
        */
        
        if (!design) {
            await customAlert('Design not found', 'Error', 'error');
            return;
        }
        
        // Check for unsaved changes
        if (hasUnsavedChanges && placedElements.length > 0) {
            const shouldContinue = await customConfirm(
                'You have unsaved changes. Loading this design will discard them. Continue?',
                'Unsaved Changes'
            );
            if (!shouldContinue) return;
        }
        
        // Clear current design
        if (interactionManager) {
            interactionManager.clearAll();
        }
        placedElements = [];
        
        // Restore room type
        if (design.roomType) {
            const roomTypeSelect = document.getElementById('roomTypeDesign');
            if (roomTypeSelect) {
                roomTypeSelect.value = design.roomType;
            }
        }
        
        // Restore objects
        if (design.objects && design.objects.length > 0) {
            design.objects.forEach(obj => {
                if (objectLoader && threeScene) {
                    const object = objectLoader.loadObject(obj.type, obj.fengShui);
                    object.position.copy(obj.position);
                    object.rotation.y = obj.rotation;
                    
                    // Mark as fixed so it can be unlocked and edited
                    object.userData.isFixed = true;
                    object.userData.isGhost = false;
                    
                    threeScene.addObject(object);
                    
                    placedElements.push({
                        type: obj.type,
                        position: obj.position,
                        fengShui: obj.fengShui
                    });
                }
            });
            
            updatePlacedItemsList();
            updateItemCount();
        }
        
        // Set editing state
        currentEditingDesignId = design.id;
        currentEditingDesignName = design.name;
        hasUnsavedChanges = false;
        
        closeHistoryModal();
        showToast(`Now editing "${design.name}". Double-click objects to unlock and reposition them.`, 'info', 5000);
        
    } catch (error) {
        console.error('Failed to load design:', error);
        await customAlert('Failed to load design. Please try again.', 'Load Failed', 'error');
    }
}

async function deleteDesignById(designId) {
    const confirmed = await customConfirm(
        'Are you sure you want to delete this design? This action cannot be undone.',
        'Delete Design?'
    );
    
    if (!confirmed) return;
    
    try {
        // For now, delete from localStorage (will be replaced with backend API)
        let savedDesigns = JSON.parse(localStorage.getItem('fengshui_saved_designs') || '[]');
        savedDesigns = savedDesigns.filter(d => d.id !== designId);
        localStorage.setItem('fengshui_saved_designs', JSON.stringify(savedDesigns));
        
        // TODO: Replace with actual backend API call
        /*
        const response = await fetch(`/api/delete-design/${designId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${getUserToken()}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to delete design');
        */
        
        // Clear editing state if this was the current design
        if (currentEditingDesignId === designId) {
            currentEditingDesignId = null;
            currentEditingDesignName = null;
        }
        
        // Refresh the modal
        showHistoryModal();
        showToast('Design deleted successfully', 'success');
        
    } catch (error) {
        console.error('Failed to delete design:', error);
        await customAlert('Failed to delete design. Please try again.', 'Delete Failed', 'error');
    }
}

function updatePlacedItemsList() {
    const list = document.getElementById('placedItemsList');
    
    if (!list) return;
    
    if (placedElements.length === 0) {
        list.innerHTML = '<p class="empty-list">No items placed yet</p>';
        return;
    }
    
    list.innerHTML = placedElements.map((item, index) => `
        <div class="placed-item">
            <span class="item-icon">${getElementIcon(item.type)}</span>
            <span class="item-name">${formatElementName(item.type)}</span>
            <span class="item-element">${item.fengShui.element}</span>
        </div>
    `).join('');
}

function updateItemCount() {
    const itemCountEl = document.getElementById('itemCount');
    if (itemCountEl) {
        itemCountEl.textContent = placedElements.length;
    }
}

// Filter elements
function filterCategory(category) {
    const items = document.querySelectorAll('.element-item');
    const categories = document.querySelectorAll('.category');
    
    // Update active category
    categories.forEach(cat => cat.classList.remove('active'));
    const active = document.querySelector(`.category[data-category="${category}"]`);
    if (active) {
        active.classList.add('active');
    }
    
    items.forEach(item => {
        if (category === 'all' || item.getAttribute('data-category') === category) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

function filterElements() {
    const searchTerm = document.getElementById('elementSearch').value.toLowerCase();
    const items = document.querySelectorAll('.element-item');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// ==================== OBSOLETE LOCAL CALCULATIONS (NOT USED) ====================
// The functions below are NO LONGER USED - Analysis now uses backend AI at /api/indoor-analyze
// The active backend-connected analyzeDesign() function is at line 320
// These are kept for reference but are not called anywhere in the code

/* DEPRECATED - DO NOT USE
function calculateDesignFengShui(elements, roomType) {
    // Calculate element balance
    const elementCounts = { wood: 0, fire: 0, earth: 0, metal: 0, water: 0 };
    const energyBalance = { yin: 0, yang: 0 };
    
    elements.forEach(item => {
        const data = elementFengShuiData[item.type];
        if (data) {
            elementCounts[data.element]++;
            energyBalance[data.energy === 'neutral' ? 'yin' : data.energy]++;
        }
    });
    
    // Calculate scores
    const elementBalance = calculateElementBalanceScore(elementCounts);
    const energyScore = calculateEnergyBalanceScore(energyBalance);
    const spacialScore = calculateSpacialScore(elements);
    const functionalScore = calculateFunctionalScore(elements, roomType);
    
    const overallScore = Math.round(
        (elementBalance * 0.3) +
        (energyScore * 0.25) +
        (spacialScore * 0.25) +
        (functionalScore * 0.20)
    );
    
    return {
        overallScore,
        elementBalance,
        energyScore,
        spacialScore,
        functionalScore,
        elementCounts,
        energyBalance,
        recommendations: generateRecommendations(elementCounts, energyBalance, elements, roomType)
    };
}

function calculateElementBalanceScore(counts) {
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    if (total === 0) return 0;
    
    // Ideal is balanced distribution
    const ideal = total / 5;
    const variance = Object.values(counts).reduce((sum, count) => {
        return sum + Math.abs(count - ideal);
    }, 0);
    
    const score = Math.max(0, 100 - (variance / total) * 50);
    return Math.round(score);
}

function calculateEnergyBalanceScore(energy) {
    const total = energy.yin + energy.yang;
    if (total === 0) return 50;
    
    const ratio = energy.yang / total;
    // Ideal ratio is 40-60% yang
    if (ratio >= 0.4 && ratio <= 0.6) {
        return 100;
    } else if (ratio >= 0.3 && ratio <= 0.7) {
        return 80;
    } else {
        return 60;
    }
}

function calculateSpacialScore(elements) {
    // Check for clutter (too many elements in small space)
    const elementDensity = elements.length;
    
    if (elementDensity < 5) return 90;
    if (elementDensity < 10) return 85;
    if (elementDensity < 15) return 75;
    if (elementDensity < 20) return 65;
    return 50; // Too cluttered
}

function calculateFunctionalScore(elements, roomType) {
    const types = elements.map(e => e.type);
    let score = 70; // Base score
    
    // Room-specific requirements
    if (roomType === 'bedroom') {
        if (types.includes('bed')) score += 10;
        if (types.includes('plant')) score += 5;
        if (types.includes('mirror') && types.includes('bed')) score -= 10; // Mirror facing bed is bad
        if (types.includes('lamp')) score += 5;
    } else if (roomType === 'living') {
        if (types.includes('sofa')) score += 10;
        if (types.includes('plant')) score += 5;
        if (types.includes('lamp') || types.includes('chandelier')) score += 5;
    } else if (roomType === 'office') {
        if (types.includes('desk')) score += 10;
        if (types.includes('chair')) score += 5;
        if (types.includes('plant')) score += 5;
        if (types.includes('bookshelf')) score += 5;
    }
    
    return Math.min(100, score);
}

function generateRecommendations(elements, energy, placed, roomType) {
    const recommendations = [];
    
    // Element recommendations
    if (elements.wood < 2) recommendations.push('Add more wood elements (plants, furniture) for growth energy');
    if (elements.fire === 0) recommendations.push('Include fire elements (candles, red colors) for passion and warmth');
    if (elements.water === 0) recommendations.push('Add water elements (fountain, mirror) for flow and prosperity');
    if (elements.earth < 2) recommendations.push('Incorporate earth elements (crystals, pottery) for stability');
    if (elements.metal === 0) recommendations.push('Include metal elements (clocks, metal frames) for clarity');
    
    // Energy recommendations
    const totalEnergy = energy.yin + energy.yang;
    const yangRatio = energy.yang / totalEnergy;
    
    if (yangRatio > 0.7) {
        recommendations.push('Balance yang energy with softer, yin elements (curtains, rugs)');
    } else if (yangRatio < 0.3) {
        recommendations.push('Add more yang energy with lighting and active elements');
    }
    
    // Room-specific
    if (roomType === 'bedroom') {
        if (!placed.some(e => e.type === 'plant')) {
            recommendations.push('Add plants for fresh air and positive energy');
        }
        if (placed.some(e => e.type === 'mirror')) {
            recommendations.push('⚠️ Avoid placing mirrors directly facing the bed');
        }
    }
    
    if (placed.length > 15) {
        recommendations.push('Consider decluttering - too many items can block energy flow');
    }
    
    if (recommendations.length === 0) {
        recommendations.push('✓ Your room design shows good feng shui balance!');
    }
    
    return recommendations;
}

function displayDesignResults(analysis) {
    const resultsSection = document.getElementById('designResults');
    resultsSection.style.display = 'block';
    
    // Build factors array from analysis
    const factors = [];
    
    // Five Elements Balance Card
    const elementCurrentItems = [];
    Object.entries(analysis.elementCounts).forEach(([element, count]) => {
        if (count > 0) {
            const names = { wood: 'Wood', fire: 'Fire', earth: 'Earth', metal: 'Metal', water: 'Water' };
            elementCurrentItems.push(`${names[element]}: ${count} items`);
        }
    });
    
    const elementImprovements = [];
    if (analysis.elementCounts.wood < 2) elementImprovements.push('Add more wood elements (plants, furniture)');
    if (analysis.elementCounts.fire === 0) elementImprovements.push('Include fire elements (lighting, warm colors)');
    if (analysis.elementCounts.water === 0) elementImprovements.push('Add water elements (fountain, mirror)');
    if (analysis.elementCounts.earth < 2) elementImprovements.push('Incorporate earth elements (crystals, pottery)');
    if (analysis.elementCounts.metal === 0) elementImprovements.push('Include metal elements (clocks, frames)');
    
    factors.push({
        title: 'Five Elements Balance',
        score: analysis.elementBalance,
        confidence: 'High',
        dataSources: ['Room Layout', 'Element Types'],
        mainIssue: analysis.elementBalance < 60 ? 'Limited element diversity in current design' : 'Element distribution is reasonable',
        current: elementCurrentItems.length > 0 ? elementCurrentItems : ['No elements placed yet'],
        improve: elementImprovements.length > 0 ? elementImprovements : ['Elements are well balanced']
    });
    
    // Yin-Yang Energy Card
    const totalEnergy = analysis.energyBalance.yin + analysis.energyBalance.yang;
    const yinPercent = totalEnergy > 0 ? Math.round((analysis.energyBalance.yin / totalEnergy) * 100) : 0;
    const yangPercent = totalEnergy > 0 ? Math.round((analysis.energyBalance.yang / totalEnergy) * 100) : 0;
    
    const energyImprovements = [];
    if (yangPercent > 70) energyImprovements.push('Add softer, yin elements (curtains, rugs, soft lighting)');
    else if (yangPercent < 30) energyImprovements.push('Add more yang energy (lighting, active elements, bright colors)');
    else energyImprovements.push('Fine-tune balance with complementary elements');
    
    factors.push({
        title: 'Yin-Yang Energy Balance',
        score: analysis.energyScore,
        confidence: 'High',
        dataSources: ['Element Properties', 'Energy Distribution'],
        mainIssue: analysis.energyScore < 60 ? `Energy imbalance detected: ${yangPercent}% yang vs ${yinPercent}% yin` : 'Energy balance is maintained',
        current: [
            `Yin energy: ${yinPercent}% (${analysis.energyBalance.yin} items)`,
            `Yang energy: ${yangPercent}% (${analysis.energyBalance.yang} items)`
        ],
        improve: energyImprovements
    });
    
    // Space Flow Card
    factors.push({
        title: 'Space Flow & Circulation',
        score: analysis.spacialScore,
        confidence: 'Medium',
        dataSources: ['Spatial Density', 'Element Count'],
        mainIssue: analysis.spacialScore < 70 ? 'Space may be cluttered, affecting energy flow' : 'Spatial arrangement supports good flow',
        current: [
            `${placedElements.length} elements placed`,
            analysis.spacialScore >= 80 ? 'Good spatial distribution' : 'Space needs attention'
        ],
        improve: analysis.spacialScore < 75 ? [
            placedElements.length > 15 ? 'Consider decluttering - remove unnecessary items' : 'Ensure clear pathways for energy flow',
            'Leave 30-40% of space open for Qi circulation'
        ] : ['Space flow is optimized']
    });
    
    // Functional Layout Card
    factors.push({
        title: 'Functional Layout',
        score: analysis.functionalScore,
        confidence: 'High',
        dataSources: ['Room Type', 'Furniture Placement'],
        mainIssue: analysis.functionalScore < 70 ? 'Layout may not fully support room purpose' : 'Layout aligns well with intended function',
        current: analysis.functionalScore >= 75 ? ['Room layout matches purpose well', 'Key furniture properly placed'] : ['Layout needs optimization'],
        improve: analysis.functionalScore < 75 ? 
            ['Add essential furniture for room type', 'Optimize placement for daily use', 'Ensure commanding position for key furniture'] :
            ['Layout is functionally sound']
    });
    
    // Build scores object
    const scores = {
        overall: analysis.overallScore,
        element_balance: analysis.elementBalance,
        energy_balance: analysis.energyScore,
        space_flow: analysis.spacialScore,
        functional_layout: analysis.functionalScore,
        wood: Math.min(100, analysis.elementCounts.wood * 20),
        fire: Math.min(100, analysis.elementCounts.fire * 20),
        earth: Math.min(100, analysis.elementCounts.earth * 20),
        metal: Math.min(100, analysis.elementCounts.metal * 20),
        water: Math.min(100, analysis.elementCounts.water * 20)
    };
    
    // Build five elements object
    const fiveElements = {
        wood: Math.min(100, analysis.elementCounts.wood * 20),
        fire: Math.min(100, analysis.elementCounts.fire * 20),
        earth: Math.min(100, analysis.elementCounts.earth * 20),
        metal: Math.min(100, analysis.elementCounts.metal * 20),
        water: Math.min(100, analysis.elementCounts.water * 20)
    };
    
    // Call the new render function
    renderIndoorResults({
        scores: scores,
        factors: factors,
        fiveElements: fiveElements,
        summary: `Your room design has been analyzed with an overall score of ${analysis.overallScore}/100.`,
        suggestions: analysis.recommendations
    });
    
    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}
END OF DEPRECATED CODE */

// ==================== UTILITY FUNCTIONS ====================

function getRating(score) {
    if (score >= 90) return { text: 'Excellent Feng Shui!', color: '#00A99D' };
    if (score >= 75) return { text: 'Good Balance', color: '#00A99D' };
    if (score >= 60) return { text: 'Fair - Room for Improvement', color: '#f59e0b' };
    return { text: 'Needs Improvement', color: '#ef4444' };
}

// ==================== UPLOAD MODE ====================

function previewPhoto(direction, input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            uploadedPhotos[direction] = e.target.result;
            updatePhotoPreview(direction, e.target.result, '✓ Uploaded');
            checkUploadComplete();
        };
        reader.readAsDataURL(file);
    }
}

function updatePhotoPreview(direction, dataUrl, labelText = '✓ Uploaded') {
    const directionLabel = direction.charAt(0).toUpperCase() + direction.slice(1);
    const preview = document.getElementById(`preview${directionLabel}`);
    const label = document.getElementById(`label${directionLabel}`);
    if (preview) {
        preview.innerHTML = `<img src="${dataUrl}" alt="${direction} view">`;
        preview.style.display = 'block';
    }
    if (label) {
        label.textContent = labelText;
        label.style.background = '#00A99D';
    }
}

function setCameraStatus(message) {
    const statusEl = document.getElementById('cameraStatusText');
    if (statusEl) {
        statusEl.textContent = message;
    }
}

function updateCameraButtons({
    canStartCamera = true,
    canStartRecording = false,
    canStopRecording = false,
    canStopCamera = false,
    canCaptureDirection = false,
    canRetakeDirection = false
} = {}) {
    const startCameraBtn = document.getElementById('startCameraBtn');
    const startRecordingBtn = document.getElementById('startRecordingBtn');
    const stopRecordingBtn = document.getElementById('stopRecordingBtn');
    const stopCameraBtn = document.getElementById('stopCameraBtn');
    const captureDirectionBtn = document.getElementById('captureDirectionBtn');
    const retakeDirectionBtn = document.getElementById('retakeDirectionBtn');

    if (startCameraBtn) startCameraBtn.disabled = !canStartCamera;
    if (startRecordingBtn) startRecordingBtn.disabled = !canStartRecording;
    if (stopRecordingBtn) stopRecordingBtn.disabled = !canStopRecording;
    if (stopCameraBtn) stopCameraBtn.disabled = !canStopCamera;
    if (captureDirectionBtn) captureDirectionBtn.disabled = !canCaptureDirection;
    if (retakeDirectionBtn) retakeDirectionBtn.disabled = !canRetakeDirection;
}

function toTitleCase(value) {
    return value ? value.charAt(0).toUpperCase() + value.slice(1) : '';
}

function setCurrentCameraDirection(direction) {
    const index = cameraDirections.indexOf(direction);
    currentCameraDirectionIndex = index >= 0 ? index : 0;
    updateCameraDirectionUI();
}

function getCurrentCameraDirection() {
    return cameraDirections[currentCameraDirectionIndex] || 'north';
}

function updateCameraDirectionUI() {
    const currentDirection = getCurrentCameraDirection();
    const currentDirectionEl = document.getElementById('cameraCurrentDirection');
    if (currentDirectionEl) {
        currentDirectionEl.textContent = toTitleCase(currentDirection);
    }

    cameraDirections.forEach((direction) => {
        const chipId = `dirChip${toTitleCase(direction)}`;
        const chip = document.getElementById(chipId);
        if (!chip) return;

        chip.classList.toggle('active', direction === currentDirection);
        chip.classList.toggle('captured', cameraCapturedDirections.has(direction));
    });
}

function selectCameraDirection(direction) {
    setCurrentCameraDirection(direction);
    setCameraStatus(`Ready to capture ${toTitleCase(direction)} view. Hold phone steady and capture.`);
}

function getFirstMissingCameraDirection() {
    return cameraDirections.find(direction => !uploadedPhotos[direction]) || null;
}

function setNextPreferredDirection() {
    const missingDirection = getFirstMissingCameraDirection();
    if (missingDirection) {
        setCurrentCameraDirection(missingDirection);
    } else {
        setCurrentCameraDirection('north');
    }
}

function estimateFrameSharpness(context, width, height) {
    const sampleW = Math.max(160, Math.floor(width / 4));
    const sampleH = Math.max(120, Math.floor(height / 4));
    const imageData = context.getImageData(0, 0, sampleW, sampleH).data;

    let totalGradient = 0;
    let count = 0;

    for (let y = 1; y < sampleH; y++) {
        for (let x = 1; x < sampleW; x++) {
            const idx = (y * sampleW + x) * 4;
            const leftIdx = (y * sampleW + (x - 1)) * 4;
            const upIdx = ((y - 1) * sampleW + x) * 4;

            const gray = (imageData[idx] + imageData[idx + 1] + imageData[idx + 2]) / 3;
            const grayLeft = (imageData[leftIdx] + imageData[leftIdx + 1] + imageData[leftIdx + 2]) / 3;
            const grayUp = (imageData[upIdx] + imageData[upIdx + 1] + imageData[upIdx + 2]) / 3;

            const gradient = Math.abs(gray - grayLeft) + Math.abs(gray - grayUp);
            totalGradient += gradient;
            count += 1;
        }
    }

    return count > 0 ? totalGradient / count : 0;
}

async function captureCurrentDirectionFromLiveCamera() {
    const previewEl = document.getElementById('roomCameraPreview');
    if (!previewEl || !roomCameraStream) {
        await customAlert('Please start the camera first.', 'Camera Not Ready', 'warning');
        return;
    }

    if (previewEl.readyState < 2) {
        await customAlert('Camera preview is still loading. Please wait a moment.', 'Preview Loading', 'info');
        return;
    }

    const direction = getCurrentCameraDirection();
    const canvas = document.createElement('canvas');
    canvas.width = previewEl.videoWidth || 1280;
    canvas.height = previewEl.videoHeight || 720;
    const context = canvas.getContext('2d');
    if (!context) {
        await customAlert('Failed to capture image from camera.', 'Capture Error', 'error');
        return;
    }

    context.drawImage(previewEl, 0, 0, canvas.width, canvas.height);
    const sharpness = estimateFrameSharpness(context, canvas.width, canvas.height);

    if (sharpness < 12) {
        const proceed = await customConfirm(
            `This ${toTitleCase(direction)} shot may be blurry (sharpness ${sharpness.toFixed(1)}). Use it anyway?`,
            'Low Quality Capture'
        );
        if (!proceed) {
            setCameraStatus(`Retake ${toTitleCase(direction)} with steadier camera and better light.`);
            return;
        }
    }

    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    uploadedPhotos[direction] = dataUrl;
    cameraCapturedDirections.add(direction);
    updatePhotoPreview(direction, dataUrl, '✓ Camera');
    checkUploadComplete();

    setNextPreferredDirection();
    const nextDirection = getFirstMissingCameraDirection();
    if (nextDirection) {
        setCameraStatus(`${toTitleCase(direction)} captured. Next: ${toTitleCase(nextDirection)}.`);
    } else {
        setCameraStatus('All 5 directions captured. Ready for highest-accuracy analysis.');
    }
}

function retakeCurrentDirection() {
    const direction = getCurrentCameraDirection();
    if (uploadedPhotos[direction]) {
        delete uploadedPhotos[direction];
        uploadedPhotos[direction] = null;
    }
    cameraCapturedDirections.delete(direction);

    const directionLabel = toTitleCase(direction);
    const preview = document.getElementById(`preview${directionLabel}`);
    const label = document.getElementById(`label${directionLabel}`);
    if (preview) {
        preview.innerHTML = '';
        preview.style.display = 'none';
    }
    if (label) {
        label.textContent = 'Click to Upload';
        label.style.background = '';
    }

    checkUploadComplete();
    updateCameraDirectionUI();
    setCameraStatus(`${directionLabel} reset. Capture it again for accurate scoring.`);
}

async function startRoomCamera() {
    const previewEl = document.getElementById('roomCameraPreview');
    const recordedEl = document.getElementById('roomRecordedPreview');

    if (!previewEl) return;

    try {
        if (roomCameraStream) {
            setCameraStatus('Camera already running.');
            updateCameraButtons({
                canStartCamera: false,
                canStartRecording: true,
                canStopRecording: false,
                canStopCamera: true,
                canCaptureDirection: true,
                canRetakeDirection: true
            });
            return;
        }

        roomCameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: 'environment' },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        });

        previewEl.style.display = 'block';
        previewEl.srcObject = roomCameraStream;
        if (recordedEl) {
            recordedEl.style.display = 'none';
            recordedEl.pause();
            recordedEl.removeAttribute('src');
            recordedEl.load();
        }

        setNextPreferredDirection();
        const nextDirection = getCurrentCameraDirection();
        setCameraStatus(`Camera is live. Capture ${toTitleCase(nextDirection)} first, then continue all directions.`);
        updateCameraButtons({
            canStartCamera: false,
            canStartRecording: true,
            canStopRecording: false,
            canStopCamera: true,
            canCaptureDirection: true,
            canRetakeDirection: true
        });
    } catch (error) {
        console.error('Failed to start room camera:', error);
        setCameraStatus('Unable to access camera. Please allow camera permission.');
        await customAlert(
            'Could not access your camera. Please allow camera access in browser settings and try again.',
            'Camera Permission Needed',
            'warning'
        );
    }
}

function stopRoomCamera() {
    if (roomMediaRecorder && roomMediaRecorder.state === 'recording') {
        roomMediaRecorder.stop();
    }

    if (roomCameraStream) {
        roomCameraStream.getTracks().forEach(track => track.stop());
        roomCameraStream = null;
    }

    const previewEl = document.getElementById('roomCameraPreview');
    if (previewEl) {
        previewEl.srcObject = null;
    }

    setCameraStatus('Camera stopped. You can start it again or analyze extracted frames.');
    updateCameraButtons({
        canStartCamera: true,
        canStartRecording: false,
        canStopRecording: false,
        canStopCamera: false,
        canCaptureDirection: false,
        canRetakeDirection: false
    });
}

function getSupportedRecordingMimeType() {
    const candidates = [
        'video/webm;codecs=vp9,opus',
        'video/webm;codecs=vp8,opus',
        'video/webm',
        'video/mp4'
    ];

    if (typeof MediaRecorder === 'undefined' || typeof MediaRecorder.isTypeSupported !== 'function') {
        return '';
    }

    for (const mimeType of candidates) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
            return mimeType;
        }
    }

    return '';
}

async function startRoomRecording() {
    if (!roomCameraStream) {
        await startRoomCamera();
    }

    if (!roomCameraStream) {
        return;
    }

    try {
        roomRecordedChunks = [];
        roomRecordedBlob = null;

        const mimeType = getSupportedRecordingMimeType();
        const recorderOptions = mimeType ? { mimeType } : undefined;
        roomMediaRecorder = new MediaRecorder(roomCameraStream, recorderOptions);

        roomMediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                roomRecordedChunks.push(event.data);
            }
        };

        roomMediaRecorder.onstop = async () => {
            const fallbackType = mimeType || roomRecordedChunks[0]?.type || 'video/webm';
            roomRecordedBlob = new Blob(roomRecordedChunks, { type: fallbackType });
            await renderRecordedVideoPreview();
            await extractFramesFromRecordedVideo(roomRecordedBlob);
        };

        roomMediaRecorder.start(300);

        setCameraStatus('Recording in progress. Move slowly across the room, then tap Stop Recording.');
        updateCameraButtons({
            canStartCamera: false,
            canStartRecording: false,
            canStopRecording: true,
            canStopCamera: true
        });
    } catch (error) {
        console.error('Failed to start recording:', error);
        setCameraStatus('Recording failed to start. Try restarting the camera.');
        customAlert('Could not start video recording. Please try again.', 'Recording Error', 'error');
    }
}

function stopRoomRecording() {
    if (roomMediaRecorder && roomMediaRecorder.state === 'recording') {
        roomMediaRecorder.stop();
        setCameraStatus('Processing video and extracting analysis frames...');
        updateCameraButtons({
            canStartCamera: false,
            canStartRecording: false,
            canStopRecording: false,
            canStopCamera: true
        });
    }
}

async function renderRecordedVideoPreview() {
    const previewEl = document.getElementById('roomCameraPreview');
    const recordedEl = document.getElementById('roomRecordedPreview');
    if (!recordedEl || !roomRecordedBlob) return;

    if (roomRecordedPreviewUrl) {
        URL.revokeObjectURL(roomRecordedPreviewUrl);
        roomRecordedPreviewUrl = null;
    }

    roomRecordedPreviewUrl = URL.createObjectURL(roomRecordedBlob);
    recordedEl.src = roomRecordedPreviewUrl;
    recordedEl.style.display = 'block';
    if (previewEl) {
        previewEl.style.display = 'none';
    }
}

function waitForVideoEvent(video, eventName) {
    return new Promise((resolve) => {
        const handler = () => {
            video.removeEventListener(eventName, handler);
            resolve();
        };
        video.addEventListener(eventName, handler, { once: true });
    });
}

async function captureFrameAt(video, canvas, context, timestampSeconds) {
    const target = Math.max(0, Math.min(timestampSeconds, Math.max(video.duration - 0.01, 0)));
    video.currentTime = target;
    await waitForVideoEvent(video, 'seeked');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.86);
}

async function extractFramesFromRecordedVideo(videoBlob) {
    if (!videoBlob || videoBlob.size === 0) {
        setCameraStatus('Recording is empty. Please record again.');
        return;
    }

    const tempVideo = document.createElement('video');
    tempVideo.preload = 'auto';
    tempVideo.muted = true;
    tempVideo.playsInline = true;
    const tempUrl = URL.createObjectURL(videoBlob);
    tempVideo.src = tempUrl;

    try {
        await waitForVideoEvent(tempVideo, 'loadedmetadata');

        const duration = Number.isFinite(tempVideo.duration) && tempVideo.duration > 0
            ? tempVideo.duration
            : 5;
        const directions = ['north', 'south', 'east', 'west', 'floor'];

        const canvas = document.createElement('canvas');
        canvas.width = tempVideo.videoWidth || 1280;
        canvas.height = tempVideo.videoHeight || 720;
        const context = canvas.getContext('2d');
        if (!context) {
            throw new Error('Canvas context unavailable for frame extraction');
        }

        for (let i = 0; i < directions.length; i++) {
            // Spread frame sampling between 12% and 88% of the clip.
            const ratio = 0.12 + (i * 0.19);
            const timestamp = duration * ratio;
            const dataUrl = await captureFrameAt(tempVideo, canvas, context, timestamp);
            const direction = directions[i];
            uploadedPhotos[direction] = dataUrl;
            cameraCapturedDirections.add(direction);
            updatePhotoPreview(direction, dataUrl, '✓ From Video');
        }

        checkUploadComplete();
        setNextPreferredDirection();
        setCameraStatus('Video processed. 5 directional frames extracted and ready for analysis.');
        updateCameraButtons({
            canStartCamera: false,
            canStartRecording: true,
            canStopRecording: false,
            canStopCamera: true,
            canCaptureDirection: true,
            canRetakeDirection: true
        });
    } catch (error) {
        console.error('Failed to extract video frames:', error);
        setCameraStatus('Could not extract frames. Please re-record with better lighting.');
        await customAlert(
            'Failed to process recorded video frames. Please try recording again in better light and with slower movement.',
            'Video Processing Error',
            'error'
        );
    } finally {
        URL.revokeObjectURL(tempUrl);
    }
}

function checkUploadComplete() {
    const uploadCount = Object.values(uploadedPhotos).filter(photo => photo !== null).length;
    const btn = document.getElementById('analyzePhotosBtn');
    
    if (uploadCount >= 3) {
        btn.disabled = false;
    } else {
        btn.disabled = true;
    }
}

function resetUpload() {
    uploadedPhotos = { north: null, south: null, east: null, west: null, floor: null };
    cameraCapturedDirections.clear();
    currentCameraDirectionIndex = 0;
    roomRecordedBlob = null;

    if (roomRecordedPreviewUrl) {
        URL.revokeObjectURL(roomRecordedPreviewUrl);
        roomRecordedPreviewUrl = null;
    }
    
    ['North', 'South', 'East', 'West', 'Floor'].forEach(dir => {
        const input = document.getElementById(`photo${dir}`);
        const preview = document.getElementById(`preview${dir}`);
        const label = document.getElementById(`label${dir}`);
        
        if (input) input.value = '';
        if (preview) {
            preview.innerHTML = '';
            preview.style.display = 'none';
        }
        if (label) {
            label.textContent = 'Click to Upload';
            label.style.background = '';
        }
    });
    
    document.getElementById('analyzePhotosBtn').disabled = true;
    document.getElementById('uploadResults').style.display = 'none';

    const recordedEl = document.getElementById('roomRecordedPreview');
    const cameraPreview = document.getElementById('roomCameraPreview');
    if (recordedEl) {
        recordedEl.pause();
        recordedEl.removeAttribute('src');
        recordedEl.style.display = 'none';
        recordedEl.load();
    }
    if (cameraPreview) {
        cameraPreview.style.display = roomCameraStream ? 'block' : 'none';
    }

    setCameraStatus('Camera is not started.');
    updateCameraDirectionUI();
}

async function analyzePhotos() {
    const btn = document.getElementById('analyzePhotosBtn');
    if (!btn) return;

    const roomType = 'general';
    const uploadedCount = Object.values(uploadedPhotos).filter(photo => photo !== null).length;
    const hasGuidedCameraCaptures = cameraCapturedDirections.size > 0;
    if (uploadedCount < 3) {
        await customAlert('Please upload at least 3 photos before analysis.', 'More Photos Needed', 'warning');
        return;
    }

    if (hasGuidedCameraCaptures && uploadedCount < 5) {
        const continueWithLowerAccuracy = await customConfirm(
            'For highest accuracy, capture all 5 directions (north, south, east, west, floor). Continue with fewer photos?',
            'Higher Accuracy Recommended'
        );
        if (!continueWithLowerAccuracy) {
            return;
        }
    }

    btn.disabled = true;
    btn.textContent = 'Analyzing Photos...';

    try {
        const source = hasGuidedCameraCaptures
            ? 'camera_guided'
            : (roomRecordedBlob ? 'camera_video' : 'photo_upload');
        const response = await fetch('https://fengshui-ai.onrender.com/api/indoor-photo-analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                roomType,
                source,
                photos: uploadedPhotos
            })
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.error || `Photo analysis failed (${response.status})`);
        }

        displayUploadResults(result.data);
        document.getElementById('uploadResults').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Photo analysis failed:', error);
        await customAlert(
            error.message || 'Photo analysis failed. Please ensure backend server is running.',
            'Analysis Error',
            'error'
        );
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze Room';
    }
}

function displayUploadResults(analysis) {
    const resultsSection = document.getElementById('uploadResults');
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
            dataSources: ['Photo Upload Analysis', 'Interior Lighting Heuristics'],
            mainIssue: 'Natural and artificial lighting quality influences vitality and mood in the room.',
            current: scoreMap.lighting >= 75
                ? ['Natural lighting appears supportive for daily activity']
                : ['Lighting appears uneven in some areas'],
            improve: scoreMap.lighting >= 75
                ? ['Keep primary activity zones well lit through the day']
                : ['Increase daylight access and add layered warm lighting']
        },
        {
            title: 'Space Flow & Circulation',
            score: scoreMap.space_flow,
            confidence: 'Medium',
            dataSources: ['Photo Upload Analysis', 'Qi Flow Principles'],
            mainIssue: 'Circulation routes should remain open to maintain healthy qi movement.',
            current: scoreMap.space_flow >= 70
                ? ['General circulation appears reasonably open']
                : ['Some movement paths look blocked or narrow'],
            improve: scoreMap.space_flow >= 70
                ? ['Maintain open pathways between entry and key zones']
                : ['Clear obstacles from primary paths and reduce crowding']
        },
        {
            title: 'Color Harmony',
            score: scoreMap.color_harmony,
            confidence: 'Medium',
            dataSources: ['Photo Upload Analysis', 'Five Elements Color Mapping'],
            mainIssue: 'Color and material balance affects emotional comfort and element harmony.',
            current: scoreMap.color_harmony >= 68
                ? ['Color tones appear relatively balanced']
                : ['Color balance appears inconsistent across areas'],
            improve: scoreMap.color_harmony >= 68
                ? ['Preserve element balance when adding new decor']
                : ['Add grounding earth/wood tones to balance dominant colors']
        },
        {
            title: 'Furniture Placement',
            score: scoreMap.furniture_placement,
            confidence: 'Medium',
            dataSources: ['Photo Upload Analysis', 'Command Position Rules'],
            mainIssue: 'Major furniture should support command view and avoid blocking energy flow.',
            current: scoreMap.furniture_placement >= 70
                ? ['Main furniture placement appears mostly functional']
                : ['Some key furniture appears suboptimal in position'],
            improve: scoreMap.furniture_placement >= 70
                ? ['Keep anchor furniture aligned with room entry visibility']
                : ['Reposition key furniture for better command and openness']
        },
        {
            title: 'Declutter & Organization',
            score: scoreMap.declutter,
            confidence: 'Medium',
            dataSources: ['Photo Upload Analysis', 'Clutter Impact Model'],
            mainIssue: 'Visual clutter can slow qi flow and reduce calmness.',
            current: scoreMap.declutter >= 65
                ? ['Organization level appears adequate']
                : ['Clutter may be reducing comfort and clarity'],
            improve: scoreMap.declutter >= 65
                ? ['Maintain simple storage and visible order']
                : ['Remove non-essential items and improve closed storage use']
        }
    ];

    const analysisCards = document.getElementById('uploadAnalysisCards');
    if (analysisCards) {
        analysisCards.innerHTML = `
            <div class="insights-header">
                <h3>Feng Shui AI Insights</h3>
                <p>Model-guided interpretation of photo-detected indoor factors, including score evidence and prioritized correction points.</p>
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

    const dashboard = document.getElementById('uploadDashboard');
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

    renderRadarChart('uploadElementsRadarChart', fiveElements);

    const elementAnalysis = document.getElementById('uploadElementAnalysis');
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

    const recommendations = document.getElementById('uploadRecommendations');
    if (recommendations && Array.isArray(analysis.recommendations)) {
        recommendations.innerHTML = analysis.recommendations.map(rec => `
            <div class="recommendation-item" style="display:flex; gap:10px; padding:10px 12px; background:#f8fbf9; border-radius:10px; margin-bottom:10px;">
                <span>💡</span>
                <p style="margin:0; color: var(--ei-text);">${escapeHtml(rec)}</p>
            </div>
        `).join('');
    }

    publishIndoorChatbotData(buildUploadChatbotData(analysis, factors, fiveElements));

    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

// ==================== CUSTOM MODAL SYSTEM ====================

// Custom Alert
function customAlert(message, title = 'Notification', type = 'info') {
    return new Promise((resolve) => {
        const modal = document.getElementById('customAlertModal');
        const titleEl = document.getElementById('alertTitle');
        const messageEl = document.getElementById('alertMessage');
        const iconHeader = modal.querySelector('.modal-icon-header');
        const icon = document.getElementById('alertIcon');
        
        titleEl.textContent = title;
        messageEl.textContent = message;
        
        // Reset classes
        iconHeader.className = 'modal-icon-header';
        
        // Set icon and style based on type
        if (type === 'success') {
            icon.textContent = '✓';
            iconHeader.classList.add('success');
        } else if (type === 'error') {
            icon.textContent = '✕';
            iconHeader.classList.add('error');
        } else if (type === 'warning') {
            icon.textContent = '⚠️';
        } else {
            icon.textContent = 'ℹ️';
        }
        
        modal.style.display = 'flex';
        
        window.closeCustomAlert = () => {
            modal.style.display = 'none';
            resolve(true);
        };
    });
}

// Custom Confirm
function customConfirm(message, title = 'Confirm Action') {
    return new Promise((resolve) => {
        const modal = document.getElementById('customConfirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const messageEl = document.getElementById('confirmMessage');
        
        titleEl.textContent = title;
        messageEl.textContent = message;
        
        modal.style.display = 'flex';
        
        window.closeCustomConfirm = (result) => {
            modal.style.display = 'none';
            resolve(result);
        };
    });
}

// Custom Prompt
function customPrompt(message, title = 'Input Required', defaultValue = '') {
    return new Promise((resolve) => {
        const modal = document.getElementById('customPromptModal');
        const titleEl = document.getElementById('promptTitle');
        const messageEl = document.getElementById('promptMessage');
        const input = document.getElementById('promptInput');
        
        titleEl.textContent = title;
        messageEl.textContent = message;
        input.value = defaultValue;
        
        modal.style.display = 'flex';
        
        // Focus input after modal opens
        setTimeout(() => input.focus(), 100);
        
        // Handle Enter key
        const handleEnter = (e) => {
            if (e.key === 'Enter') {
                window.closeCustomPrompt('submit');
                input.removeEventListener('keydown', handleEnter);
            }
        };
        input.addEventListener('keydown', handleEnter);
        
        window.closeCustomPrompt = (action) => {
            modal.style.display = 'none';
            input.removeEventListener('keydown', handleEnter);
            
            if (action === 'submit' && input.value.trim()) {
                resolve(input.value.trim());
            } else {
                resolve(null);
            }
        };
    });
}

// Toast Notification
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    const titles = {
        success: 'Success',
        error: 'Error',
        warning: 'Warning',
        info: 'Info'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${titles[type] || titles.info}</div>
            <div class="toast-message">${message}</div>
        </div>
        <div class="toast-close" onclick="this.parentElement.remove()">×</div>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    return toast;
}

function openUploadGuideModal() {
    const modal = document.getElementById('uploadGuideModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeUploadGuideModal() {
    const modal = document.getElementById('uploadGuideModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function setupUploadGuideModalInteractions() {
    const modal = document.getElementById('uploadGuideModal');
    if (!modal) return;

    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeUploadGuideModal();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.style.display === 'flex') {
            closeUploadGuideModal();
        }
    });
}

// Handle browser back button
window.addEventListener('popstate', function(event) {
    console.log('Browser back button pressed', event.state);
    
    // If going back to selection mode or no state
    if (!event.state || event.state.mode === 'selection') {
        // Check if user has unsaved changes
        if (currentMode && placedElements.length > 0 && hasUnsavedChanges) {
            // Show confirmation
            customConfirm(
                'You have unsaved changes. Going back will discard them. Continue?',
                'Leave Current Mode?'
            ).then(confirmed => {
                if (confirmed) {
                    performBackToSelection();
                } else {
                    // User cancelled - restore the forward state
                    history.pushState({ mode: currentMode }, '', '');
                }
            });
        } else if (document.getElementById('modeSelection')) {
            performBackToSelection();
        }
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Indoor Analysis System Initialized');

    const hasModeSelection = !!document.getElementById('modeSelection');
    const hasDesignMode = !!document.getElementById('designMode');
    const hasUploadMode = !!document.getElementById('uploadMode');

    if (hasModeSelection) {
        // Split-page indoor setup: always show selector page and ignore stale mode.
        history.replaceState({ mode: 'selection' }, '', '');
        localStorage.removeItem('currentMode');
        document.getElementById('modeSelection').classList.add('active');
    } else if (hasDesignMode) {
        // Split page: design page should initialize 3D immediately.
        currentMode = 'design';
        initialize3DScene();
    } else if (hasUploadMode) {
        // Split page: upload page only needs upload mode state.
        currentMode = 'upload';

        const pageParams = new URLSearchParams(window.location.search);
        if (pageParams.get('mode') === 'camera') {
            const cameraCard = document.querySelector('.camera-capture-card');
            if (cameraCard) {
                setTimeout(() => {
                    cameraCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 120);
            }
            setCameraStatus('Camera mode selected. Tap Start Camera to begin recording.');
        }
    }

    setupUploadGuideModalInteractions();
    
    // Initialize element details panel
    clearElementDetails();
    
    // Ensure functions are globally accessible
    window.saveDesignToAccount = saveDesignToAccount;
    window.showHistoryModal = showHistoryModal;
    window.closeHistoryModal = closeHistoryModal;
    window.editDesignById = editDesignById;
    window.deleteDesignById = deleteDesignById;
    window.selectMode = selectMode;
    window.backToSelection = backToSelection;
    window.analyzeDesign = analyzeDesign;
    window.showUsedElementDetails = showUsedElementDetails;
    window.openUploadGuideModal = openUploadGuideModal;
    window.closeUploadGuideModal = closeUploadGuideModal;
    window.startRoomCamera = startRoomCamera;
    window.stopRoomCamera = stopRoomCamera;
    window.startRoomRecording = startRoomRecording;
    window.stopRoomRecording = stopRoomRecording;
    window.captureCurrentDirectionFromLiveCamera = captureCurrentDirectionFromLiveCamera;
    window.selectCameraDirection = selectCameraDirection;
    window.retakeCurrentDirection = retakeCurrentDirection;

    if (document.getElementById('uploadMode')) {
        updateCameraButtons({
            canStartCamera: true,
            canStartRecording: false,
            canStopRecording: false,
            canStopCamera: false,
            canCaptureDirection: false,
            canRetakeDirection: false
        });
        updateCameraDirectionUI();
        setCameraStatus('Camera is not started.');
    }
    
    console.log('✓ Global functions registered');
});
