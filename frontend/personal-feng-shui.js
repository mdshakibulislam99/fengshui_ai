/**
 * Personal Feng Shui Analysis
 * Handles form submission, API calls, and results display
 */

(function() {
    'use strict';

    const API_BASE_URL = 'https://fengshui-ai.onrender.com/api';
    const loadingStages = [
        'Reading your birth profile and life priorities...',
        'Balancing your five-element pattern and personal timing...',
        'Reviewing your favorable and challenging directions...',
        'Writing a practical action plan for your space...'
    ];
    
    // DOM Elements
    let form, inputSection, resultsSection, loadingOverlay, errorMessage;
    let loadingInterval = null;
    let loadingProgress = 0;
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', init);
    
    function init() {
        // Get DOM elements
        form = document.getElementById('personalFsForm');
        inputSection = document.getElementById('inputForm');
        resultsSection = document.getElementById('resultsDisplay');
        loadingOverlay = document.getElementById('loadingOverlay');
        errorMessage = document.getElementById('errorMessage');
        
        // Attach event listeners
        if (form) {
            form.addEventListener('submit', handleSubmit);
        }
        
        const backBtn = document.getElementById('backBtn');
        if (backBtn) {
            backBtn.addEventListener('click', resetForm);
        }
        
        const closeError = document.getElementById('closeError');
        if (closeError) {
            closeError.addEventListener('click', hideError);
        }
        
        const printBtn = document.getElementById('printBtn');
        if (printBtn) {
            printBtn.addEventListener('click', handlePrint);
        }
        
        const shareBtn = document.getElementById('shareBtn');
        if (shareBtn) {
            shareBtn.addEventListener('click', handleShare);
        }
        
        const saveBtn = document.getElementById('saveBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', handleSave);
        }
    }
    
    /**
     * Handle form submission
     */
    async function handleSubmit(e) {
        e.preventDefault();
        
        // Collect form data
        const formData = new FormData(form);
        const birthYear = parseInt(formData.get('birthYear'));
        const birthMonth = parseInt(formData.get('birthMonth'));
        const birthDay = parseInt(formData.get('birthDay'));
        const gender = formData.get('gender');
        const birthTime = formData.get('birthTime') || null;
        const preferredDirection = formData.get('preferredDirection') || null;
        const budget = formData.get('budget') || 'any';
        
        // Collect checkboxes
        const goals = [];
        const goalCheckboxes = document.querySelectorAll('input[name="goals"]:checked');
        goalCheckboxes.forEach(cb => goals.push(cb.value));
        
        const concerns = [];
        const concernCheckboxes = document.querySelectorAll('input[name="concerns"]:checked');
        concernCheckboxes.forEach(cb => concerns.push(cb.value));
        
        // Collect other fields
        const relationshipStatus = formData.get('relationshipStatus') || null;
        const occupation = formData.get('occupation') || null;
        const livingType = formData.get('livingType') || null;
        const yearsAtLocation = formData.get('yearsAtLocation') || null;
        const spaceFocus = formData.get('spaceFocus') || null;
        
        // Validate required fields
        if (!birthYear || !birthMonth || !birthDay || !gender) {
            showError('Please fill in all required fields (Birth Date and Gender).');
            return;
        }
        
        if (birthYear < 1900 || birthYear > 2025) {
            showError('Please enter a valid birth year between 1900 and 2025.');
            return;
        }
        
        if (birthMonth < 1 || birthMonth > 12) {
            showError('Please select a valid birth month.');
            return;
        }
        
        if (birthDay < 1 || birthDay > 31) {
            showError('Please enter a valid birth day.');
            return;
        }
        
        if (goals.length > 3) {
            showError('Please select no more than 3 life goals for best results.');
            return;
        }
        
        // Prepare request payload
        const payload = {
            profile: {
                birthYear,
                gender,
                birthMonth,
                birthDay,
                ...(birthTime && { birthTime }),
                ...(goals.length > 0 && { goals }),
                ...(preferredDirection && { preferredDirection }),
                ...(concerns.length > 0 && { concerns }),
                ...(relationshipStatus && { relationshipStatus }),
                ...(occupation && { occupation }),
                ...(livingType && { livingType }),
                ...(yearsAtLocation && { yearsAtLocation }),
                ...(spaceFocus && { spaceFocus })
            }
        };
        
        // Show loading
        showLoading();
        
        try {
            // Call API
            const response = await fetch(`${API_BASE_URL}/personal-feng-shui/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success && result.data) {
                displayResults(result.data, budget, { goals, concerns });
            } else {
                throw new Error(result.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Failed to analyze your profile. Please try again. ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    /**
     * Display analysis results
     */
    function displayResults(data, budget, userInput) {
        // Hide form, show results
        inputSection.classList.remove('active');
        resultsSection.classList.add('active');
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Overall Score with Rating
        const score = data.overall_score || 0;
        document.getElementById('overallScore').textContent = score;
        
        // Score rating text
        const ratingEl = document.getElementById('scoreRating');
        const explanationEl = document.getElementById('scoreExplanation');
        if (score >= 80) {
            ratingEl.textContent = '🌟 Excellent Harmony';
            ratingEl.style.color = '#10b981';
            explanationEl.textContent = 'Your current setup aligns very well with your Feng Shui profile!';
        } else if (score >= 60) {
            ratingEl.textContent = '✨ Good Balance';
            ratingEl.style.color = '#60a5fa';
            explanationEl.textContent = 'Decent alignment with room for improvement in some areas.';
        } else if (score >= 40) {
            ratingEl.textContent = '⚡ Moderate Alignment';
            ratingEl.style.color = '#f59e0b';
            explanationEl.textContent = 'Several adjustments needed to improve your space energy.';
        } else {
            ratingEl.textContent = 'Needs Attention';
            ratingEl.style.color = '#ef4444';
            explanationEl.textContent = 'Significant changes recommended for better harmony.';
        }
        
        animateGauge(score);
        
        // Score Breakdown from real backend values
        const scoreDetails = data.scores || {};
        setTimeout(() => {
            animateBreakdown('elementAlignBar', 'elementAlignValue', scoreDetails.element_alignment || 0);
            animateBreakdown('directionAlignBar', 'directionAlignValue', scoreDetails.direction_alignment || 0);
            animateBreakdown('goalAlignBar', 'goalAlignValue', scoreDetails.goal_alignment || 0);
        }, 500);
        
        // Personal Profile
        const profile = data.personal_profile || {};
        
        // Kua Number
        document.getElementById('kuaNumber').textContent = profile.kua_number || '-';
        document.getElementById('kuaDesc').textContent = getKuaDescription(profile.kua_number);
        const kuaGroup = profile.kua_number <= 4 || profile.kua_number === 9 ? 'East Group' : 'West Group';
        document.getElementById('kuaGroup').textContent = kuaGroup;
        
        // Element
        const elementBadge = document.getElementById('primaryElement');
        elementBadge.textContent = (profile.primary_element || 'Unknown').toUpperCase();
        elementBadge.className = 'profile-value element-badge element-' + (profile.primary_element || 'unknown').toLowerCase();
        
        document.getElementById('elementStrength').textContent = profile.element_strength ? 
            `${profile.element_strength} strength` : '-';
        
        const elementTraits = getElementTraits(profile.primary_element);
        document.getElementById('elementTraits').textContent = elementTraits;
        
        // Life Phase
        const lifePhaseData = profile.life_phase;
        const lifePhase = lifePhaseData && typeof lifePhaseData === 'object'
            ? String(lifePhaseData.phase || profile.life_phase_label || '-').replace(/_/g, ' ').toUpperCase()
            : (profile.life_phase_label || (profile.life_phase ? String(profile.life_phase).replace(/_/g, ' ').toUpperCase() : '-'));
        document.getElementById('lifePhase').textContent = lifePhase;
        const ageInfo = profile.age ? `Age ${profile.age}` : '-';
        const progress = lifePhaseData && typeof lifePhaseData === 'object' && typeof lifePhaseData.progress === 'number'
            ? ` • ${lifePhaseData.progress}% through this phase`
            : '';
        document.getElementById('ageInfo').textContent = `${ageInfo}${progress}`;
        const phaseGuidance = lifePhaseData && typeof lifePhaseData === 'object'
            ? (lifePhaseData.description || profile.life_phase_description || getPhaseGuidance(lifePhaseData.phase))
            : getPhaseGuidance(profile.life_phase);
        document.getElementById('phaseGuidance').textContent = phaseGuidance;
        
        // Zodiac
        const zodiacBranchRaw = data.bazi_analysis?.year_pillar?.branch?.name;
        const zodiacBranch = zodiacBranchRaw ? String(zodiacBranchRaw).charAt(0).toUpperCase() + String(zodiacBranchRaw).slice(1).toLowerCase() : null;
        const zodiac = getZodiacAnimal(zodiacBranch);
        document.getElementById('zodiacAnimal').textContent = zodiac.animal;
        document.getElementById('zodiacDesc').textContent = zodiac.trait;
        
        // Directions
        displayDirections(data.directions);
        
        // Recommendations
        displayRecommendations(data.recommendations, userInput);
        
        // Remedies
        displayRemedies(data.remedies, budget);
        
        // Bagua Guidance
        displayBagua(data.bagua_guidance);
        
        // Initialize recommendation tabs
        initRecommendationTabs();
    }
    
    /**
     * Animate score gauge
     */
    function animateGauge(score) {
        const gauge = document.getElementById('gaugeProgress');
        const maxOffset = 251.2; // Full circle
        const targetOffset = maxOffset - (maxOffset * score / 100);
        
        // Animate from full offset to target
        let currentOffset = maxOffset;
        const step = (maxOffset - targetOffset) / 60; // 60 frames
        
        const animate = () => {
            currentOffset -= step;
            if (currentOffset <= targetOffset) {
                currentOffset = targetOffset;
                gauge.style.strokeDashoffset = currentOffset;
                return;
            }
            gauge.style.strokeDashoffset = currentOffset;
            requestAnimationFrame(animate);
        };
        
        animate();
        
        // Update color based on score
        if (score >= 70) {
            gauge.style.stroke = '#10b981'; // Green
        } else if (score >= 40) {
            gauge.style.stroke = '#f59e0b'; // Orange
        } else {
            gauge.style.stroke = '#ef4444'; // Red
        }
    }
    
    /**
     * Display directions analysis
     */
    function displayDirections(directions) {
        if (!directions) return;
        
        const container = document.getElementById('directionsGrid');
        if (!container) return;
        container.innerHTML = '';
        
        const directionsList = Array.isArray(directions.all_directions)
            ? directions.all_directions
            : Object.entries(directions.detailed_scores || {}).map(([direction, info]) => ({
                direction,
                score: info.score,
                type: info.type,
                name: info.name,
                benefit: info.benefit,
                quality: getDirectionQuality(info.score)
            }));

        directionsList.forEach(dir => {
            const card = document.createElement('div');
            card.className = 'direction-card';
            
            let qualityClass = '';
            if (dir.score >= 80) qualityClass = 'excellent';
            else if (dir.score >= 60) qualityClass = 'good';
            else if (dir.score >= 40) qualityClass = 'moderate';
            else qualityClass = 'poor';
            
            card.innerHTML = `
                <div class="direction-compass">${dir.direction}</div>
                <div class="direction-name">${getDirFullName(dir.direction)}</div>
                <div class="direction-quality ${qualityClass}">${dir.name || dir.quality || 'Unknown'}</div>
                <div class="direction-score">${dir.score}/100</div>
                ${dir.benefit ? `<div class="direction-type">${dir.benefit}</div>` : (dir.type ? `<div class="direction-type">${dir.type}</div>` : '')}
            `;
            
            container.appendChild(card);
        });
        
        // Current direction info
        if (directions.current_direction) {
            const currentCard = document.getElementById('currentDirectionCard');
            const currentText = document.getElementById('currentDirectionText');
            if (currentCard && currentText) {
                currentCard.style.display = 'flex';
                const score = directions.current_score || 0;
                const bestDir = directions.best_direction || 'E';
                const currentInfo = directions.current_direction_info || (directions.detailed_scores || {})[directions.current_direction] || null;
                currentText.innerHTML = `
                    You are currently facing <strong>${getDirFullName(directions.current_direction)}</strong> 
                    with a score of <strong>${score}/100</strong>. 
                    ${score < 50 ? 
                        `Consider reorienting to <strong>${getDirFullName(bestDir)}</strong> for better energy flow.` :
                        `This is a favorable direction for you${currentInfo?.name ? ` (${currentInfo.name})` : ''}! ✨`}
                `;
            }
        }
    }
    
    /**
     * Display recommendations
     */
    function displayRecommendations(recommendations, userInput) {
        if (!recommendations || recommendations.length === 0) return;
        
        const container = document.getElementById('recommendationsList');
        if (!container) return;
        container.innerHTML = '';
        
        // Filter out generic fallback recommendations
        const genericPhrases = [
            'Follow classical Feng Shui principles',
            'follow feng shui',
            'classical principles',
            'traditional approach'
        ];
        
        const filteredRecs = recommendations.filter(rec => {
            const text = (rec.recommendation || rec.action || rec.description || '').toLowerCase();
            return !genericPhrases.some(phrase => text.includes(phrase.toLowerCase()));
        }).slice(0, 5);  // Max 5 recommendations
        
        if (filteredRecs.length === 0) {
            container.innerHTML = '<p style="color: #94a3b8; text-align: center; padding: 24px;">Generating personalized recommendations...</p>';
            return;
        }
        
        filteredRecs.forEach((rec, index) => {
            const item = document.createElement('div');
            item.className = 'recommendation-item';
            item.dataset.priority = rec.priority || 'low';
            
            const priorityClass = rec.priority === 'high' ? 'priority-high' : 
                                 rec.priority === 'medium' ? 'priority-medium' : 'priority-low';
            
            const title = rec.title || rec.category || 'Recommendation';
            const recommendation = rec.description || rec.recommendation || rec.action || '';
            const implementation = rec.implementation || '';
            
            item.innerHTML = `
                <div class="rec-header">
                    <span class="rec-number">${index + 1}</span>
                    <span class="rec-priority ${priorityClass}">${rec.priority || 'medium'}</span>
                </div>
                <h4 class="rec-title">${title}</h4>
                <p class="rec-description">${recommendation}</p>
                ${implementation ? `<p class="rec-implementation"><strong>How to apply:</strong>${implementation}</p>` : ''}
            `;
            
            container.appendChild(item);
        });
    }
    
    /**
     * Display remedies
     */
    function displayRemedies(remedies, userBudget) {
        if (!remedies) return;
        
        const container = document.getElementById('remediesGrid');
        if (!container) return;
        container.innerHTML = '';
        
        // Combine element remedies and budget-friendly ones
        let allRemedies = [];
        if (remedies.element_remedies) {
            allRemedies = allRemedies.concat(remedies.element_remedies);
        }
        if (remedies.budget_friendly && userBudget === 'low') {
            allRemedies = allRemedies.concat(remedies.budget_friendly);
        }
        if (remedies.recommended) {
            allRemedies = allRemedies.concat(remedies.recommended);
        }
        
        // Remove duplicates
        const uniqueRemedies = allRemedies.filter((remedy, index, self) =>
            index === self.findIndex(r => r.name === remedy.name)
        );
        
        // Show at least 6 remedies
        const displayRemedies = uniqueRemedies.slice(0, Math.max(6, uniqueRemedies.length));
        
        if (displayRemedies.length === 0) {
            container.innerHTML = '<p style="color: #94a3b8;">No specific remedies available for your profile.</p>';
            return;
        }
        
        displayRemedies.forEach(remedy => {
            const card = document.createElement('div');
            card.className = 'remedy-card';
            
            const costClass = remedy.cost === '$' ? 'cost-low' :
                             remedy.cost === '$$' ? 'cost-medium' : 'cost-high';
            
            const element = remedy.element || 'general';
            const name = remedy.name || remedy.item || 'Feng Shui Enhancement';
            const benefits = remedy.benefits || remedy.description || 'Improves energy flow';
            const placement = remedy.placement || remedy.location || '';
            const difficulty = remedy.difficulty || 'Medium';
            const cost = remedy.cost || '$$';
            
            card.innerHTML = `
                <h4 class="remedy-name">${name}</h4>
                <p class="remedy-desc">${benefits}</p>
                <div class="remedy-meta">
                    <span class="remedy-cost ${costClass}">${cost}</span>
                    <span class="remedy-difficulty">${difficulty}</span>
                </div>
                ${placement ? `<p class="remedy-placement">Placement: ${placement}</p>` : ''}
                <div class="remedy-element-tag">${element.toUpperCase()}</div>
            `;
            
            container.appendChild(card);
        });
    }
    
    /**
     * Display Bagua guidance
     */
    function displayBagua(baguaData) {
        if (!baguaData) return;
        
        const container = document.getElementById('baguaGrid');
        if (!container) return;
        container.innerHTML = '';
        
        const baguaAreas = [
            { key: 'career', name: 'Career', direction: 'North' },
            { key: 'relationships', name: 'Relationships', direction: 'Southwest' },
            { key: 'family', name: 'Family', direction: 'East' },
            { key: 'wealth', name: 'Wealth', direction: 'Southeast' },
            { key: 'health', name: 'Health', direction: 'Center' },
            { key: 'children', name: 'Children', direction: 'West' },
            { key: 'knowledge', name: 'Knowledge', direction: 'Northeast' },
            { key: 'fame', name: 'Fame', direction: 'South' },
            { key: 'helpful_people', name: 'Helpful People', direction: 'Northwest' }
        ];
        
        baguaAreas.forEach(area => {
            const data = baguaData[area.key] || {};
            
            const card = document.createElement('div');
            card.className = 'bagua-card';
            
            const element = data.element || '-';
            const guidance = data.guidance || data.aspect || data.description || `Focus on ${area.name.toLowerCase()} for balance and harmony.`;
            const colors = Array.isArray(data.colors) ? data.colors.join(', ') : (data.colors || data.color || 'Natural tones');
            const enhancements = Array.isArray(data.enhancements)
                ? data.enhancements.map(item => String(item).replace(/_/g, ' ')).join(', ')
                : (data.tips || data.enhancements || '');
            
            card.innerHTML = `
                <div class="bagua-header">
                    <h4>${area.name}</h4>
                    <span class="bagua-dir">${area.direction}</span>
                </div>
                <div class="bagua-element">
                    <strong>Element:</strong> ${element}
                </div>
                <div class="bagua-colors">
                    <strong>Colors:</strong> ${colors}
                </div>
                <p class="bagua-guidance">${guidance}</p>
                ${enhancements ? 
                    `<p class="bagua-enhancements"><strong>Tip:</strong> ${enhancements}</p>` : ''}
            `;
            
            container.appendChild(card);
        });
    }
    
    /**
     * Helper functions
     */
    function getKuaDescription(kua) {
        const descriptions = {
            1: 'Water element - Wisdom and career focus',
            2: 'Earth element - Relationships and grounding',
            3: 'Wood element - Growth and expansion',
            4: 'Wood element - Gentle progress',
            6: 'Metal element - Authority and leadership',
            7: 'Metal element - Communication and joy',
            8: 'Earth element - Stability and family',
            9: 'Fire element - Recognition and passion'
        };
        return descriptions[kua] || 'Your personal energy number';
    }
    
    function getDirFullName(abbr) {
        const names = {
            'N': 'North', 'NE': 'Northeast', 'E': 'East', 'SE': 'Southeast',
            'S': 'South', 'SW': 'Southwest', 'W': 'West', 'NW': 'Northwest'
        };
        return names[abbr] || abbr;
    }
    
    function animateBreakdown(barId, valueId, targetPercent) {
        const bar = document.getElementById(barId);
        const valueEl = document.getElementById(valueId);
        if (!bar || !valueEl) return;
        
        let current = 0;
        const step = targetPercent / 50;
        
        const animate = () => {
            current += step;
            if (current >= targetPercent) {
                current = targetPercent;
                bar.style.width = current + '%';
                valueEl.textContent = Math.round(current) + '%';
                return;
            }
            bar.style.width = current + '%';
            valueEl.textContent = Math.round(current) + '%';
            requestAnimationFrame(animate);
        };
        
        animate();
    }
    
    function getElementTraits(element) {
        const traits = {
            wood: 'Growth-oriented, creative, flexible',
            fire: 'Passionate, energetic, transformative',
            earth: 'Stable, nurturing, practical',
            metal: 'Structured, precise, determined',
            water: 'Adaptive, intuitive, flowing'
        };
        return traits[element] || 'Unique energy signature';
    }
    
    function getPhaseGuidance(phase) {
        const guidance = {
            growth: 'Focus on learning and building foundations',
            expansion: 'This phase favors career building and relationship development',
            maturity: 'A strong phase for achievement, structure, and consolidation',
            wisdom: 'A period for leadership, teaching, and strategic decisions',
            reflection: 'A phase for legacy, restoration, and deeper spiritual alignment'
        };
        return guidance[phase] || 'Navigate your life journey wisely';
    }

    function getDirectionQuality(score) {
        if (score >= 80) return 'Excellent';
        if (score >= 60) return 'Supportive';
        if (score >= 40) return 'Mixed';
        return 'Challenging';
    }
    
    function getZodiacAnimal(earthlyBranch) {
        const zodiac = {
            Rat: { animal: 'Rat', trait: 'Intelligent & resourceful' },
            Ox: { animal: 'Ox', trait: 'Diligent & dependable' },
            Tiger: { animal: 'Tiger', trait: 'Brave & confident' },
            Rabbit: { animal: 'Rabbit', trait: 'Gentle & compassionate' },
            Dragon: { animal: 'Dragon', trait: 'Powerful & charismatic' },
            Snake: { animal: 'Snake', trait: 'Wise & enigmatic' },
            Horse: { animal: 'Horse', trait: 'Energetic & free-spirited' },
            Goat: { animal: 'Goat', trait: 'Creative & calm' },
            Monkey: { animal: 'Monkey', trait: 'Clever & playful' },
            Rooster: { animal: 'Rooster', trait: 'Observant & hardworking' },
            Dog: { animal: 'Dog', trait: 'Loyal & honest' },
            Pig: { animal: 'Pig', trait: 'Generous & compassionate' }
        };
        return zodiac[earthlyBranch] || { animal: 'Profile', trait: 'Unique zodiac energy' };
    }
    
    function initRecommendationTabs() {
        const tabs = document.querySelectorAll('.rec-tab');
        const recItems = document.querySelectorAll('.recommendation-item');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const priority = tab.dataset.priority;
                
                // Filter recommendations
                recItems.forEach(item => {
                    if (priority === 'all') {
                        item.style.display = 'block';
                    } else {
                        const itemPriority = item.querySelector('.rec-priority').textContent.toLowerCase();
                        if (itemPriority.includes(priority)) {
                            item.style.display = 'block';
                        } else {
                            item.style.display = 'none';
                        }
                    }
                });
            });
        });
    }
    
    /**
     * UI helpers
     */
    function showLoading() {
        if (loadingOverlay) {
            loadingOverlay.classList.add('active');
            startLoadingProgress();
        }

        const submitBtn = form ? form.querySelector('.btn-analyze') : null;
        if (submitBtn) {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
        }
    }
    
    function hideLoading() {
        if (loadingOverlay) {
            stopLoadingProgress(true);
            loadingOverlay.classList.remove('active');
        }

        const submitBtn = form ? form.querySelector('.btn-analyze') : null;
        if (submitBtn) {
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    }

    function startLoadingProgress() {
        stopLoadingProgress(false);
        loadingProgress = 8;
        updateLoadingProgress(loadingProgress);

        loadingInterval = window.setInterval(() => {
            const next = loadingProgress < 32 ? 9 : loadingProgress < 58 ? 7 : loadingProgress < 78 ? 5 : 2;
            loadingProgress = Math.min(92, loadingProgress + next);
            updateLoadingProgress(loadingProgress);
        }, 650);
    }

    function stopLoadingProgress(complete) {
        if (loadingInterval) {
            window.clearInterval(loadingInterval);
            loadingInterval = null;
        }

        if (complete) {
            loadingProgress = 100;
            updateLoadingProgress(loadingProgress);
        }
    }

    function updateLoadingProgress(value) {
        const percentEl = document.getElementById('loadingPercent');
        const fillEl = document.getElementById('loadingProgressFill');
        const stageEl = document.getElementById('loadingStage');
        const stepLabelEl = document.getElementById('loadingStepLabel');
        const steps = document.querySelectorAll('.loading-step');
        const safeValue = Math.max(0, Math.min(100, Math.round(value)));
        const stageIndex = safeValue >= 100 ? loadingStages.length - 1 : Math.min(loadingStages.length - 1, Math.floor(safeValue / 25));

        if (percentEl) {
            percentEl.textContent = `${safeValue}%`;
        }

        if (fillEl) {
            fillEl.style.width = `${safeValue}%`;
        }

        if (stageEl) {
            stageEl.textContent = loadingStages[stageIndex];
        }

        if (stepLabelEl) {
            stepLabelEl.textContent = `Step ${Math.min(stageIndex + 1, 4)} of 4`;
        }

        steps.forEach((step, index) => {
            step.classList.toggle('is-complete', index < stageIndex || safeValue === 100);
            step.classList.toggle('is-active', index === stageIndex && safeValue < 100);
        });
    }
    
    function showError(message) {
        if (errorMessage) {
            document.getElementById('errorText').textContent = message;
            errorMessage.classList.add('active');
        }
    }
    
    function hideError() {
        if (errorMessage) {
            errorMessage.classList.remove('active');
        }
    }
    
    function resetForm() {
        inputSection.classList.add('active');
        resultsSection.classList.remove('active');
        form.reset();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    /**
     * Action handlers
     */
    function handlePrint() {
        window.print();
    }
    
    function handleShare() {
        if (navigator.share) {
            navigator.share({
                title: 'My Personal Feng Shui Analysis',
                text: 'Check out my Feng Shui profile from QiMatrix!',
                url: window.location.href
            }).catch(err => console.log('Share failed:', err));
        } else {
            // Fallback: copy link
            navigator.clipboard.writeText(window.location.href);
            alert('Link copied to clipboard!');
        }
    }
    
    function handleSave() {
        // Store results in localStorage
        const resultsData = {
            timestamp: new Date().toISOString(),
            score: document.getElementById('overallScore').textContent,
            kua: document.getElementById('kuaNumber').textContent,
            element: document.getElementById('primaryElement').textContent
        };
        
        localStorage.setItem('fengshui_profile', JSON.stringify(resultsData));
        alert('Profile saved successfully!');
    }
})();
