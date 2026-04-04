function clampScore(value) {
	const n = Number(value);
	if (!Number.isFinite(n)) return 0;
	return Math.max(0, Math.min(100, n));
}

function escapeHtml(text) {
	return String(text || '')
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;')
		.replaceAll("'", '&#039;');
}

function statusFromScore(score) {
	if (score >= 80) return 'Excellent';
	if (score >= 60) return 'Balanced';
	return 'Needs Improvement';
}

function ScoreGauge(score, subtitle = 'Overall Score') {
	const value = clampScore(score);
	return `
		<div class="score-gauge">
			<div class="gauge-ring" style="--value:${value}">
				<span class="gauge-value">${Math.round(value)}</span>
			</div>
			<div>
				<div class="section-title">${escapeHtml(subtitle)}</div>
				<div style="font-size:28px;font-weight:700;color:var(--ei-primary);line-height:1;">${Math.round(value)}</div>
				<div class="status-chip">${statusFromScore(value)}</div>
			</div>
		</div>
	`;
}

function ImprovementList(title, icon, items) {
	const values = Array.isArray(items) && items.length ? items : ['No additional points detected.'];
	const listItems = values.map(item => `<li>${escapeHtml(item)}</li>`).join('');

	return `
		<div>
			<div class="section-title">${escapeHtml(icon)} ${escapeHtml(title)}</div>
			<ul class="analysis-list">${listItems}</ul>
		</div>
	`;
}

function AnalysisCard({ title, score, current = [], missing = [], improve = [] }) {
	const numeric = clampScore(score);
	return `
		<article class="card analysis-card">
			<div class="score-row">
				<h3>${escapeHtml(title)}</h3>
				<div class="score">${Math.round(numeric)}</div>
			</div>
			<div class="progress-track"><div class="progress-fill" style="width:${numeric}%"></div></div>
			${ImprovementList('Current Condition', '✔', current)}
			${ImprovementList('What is Missing', '⚠', missing)}
			${ImprovementList('How to Improve', '🔧', improve)}
		</article>
	`;
}

function LayoutPreview() {
	return `
		<div class="layout-preview" aria-label="Environmental layout preview">
			<div class="compass">N</div>
			<div class="zone" style="left:8%;top:14%;width:34%;height:26%;">Open Space</div>
			<div class="zone" style="left:52%;top:20%;width:38%;height:24%;">Dense Block</div>
			<div class="zone" style="left:20%;top:56%;width:46%;height:30%;">Active Corridor</div>
			<div class="flow-arrow" style="left:36%;top:44%;">→</div>
			<div class="flow-arrow" style="left:60%;top:52%;">↗</div>
		</div>
	`;
}

function RadarElementChart(containerId, fiveElements = {}) {
	const canvas = document.getElementById(containerId);
	if (!canvas || typeof Chart === 'undefined') return;

	const ctx = canvas.getContext('2d');
	if (canvas.chart) {
		canvas.chart.destroy();
	}

	const labels = ['Wood', 'Fire', 'Earth', 'Metal', 'Water'];
	const data = [
		clampScore(fiveElements.wood),
		clampScore(fiveElements.fire),
		clampScore(fiveElements.earth),
		clampScore(fiveElements.metal),
		clampScore(fiveElements.water)
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

function scoreTextCards(metrics) {
	return `
		<div class="score-metrics">
			<div class="metric-pill"><span class="label">Yin-Yang</span><span class="value">${Math.round(clampScore(metrics.yinYang))}</span></div>
			<div class="metric-pill"><span class="label">Qi Flow</span><span class="value">${Math.round(clampScore(metrics.qiFlow))}</span></div>
			<div class="metric-pill"><span class="label">Elements</span><span class="value">${Math.round(clampScore(metrics.elements))}</span></div>
		</div>
	`;
}

window.OutdoorUI = {
	clampScore,
	statusFromScore,
	ScoreGauge,
	AnalysisCard,
	ImprovementList,
	RadarElementChart,
	LayoutPreview,
	scoreTextCards,
	escapeHtml
};
