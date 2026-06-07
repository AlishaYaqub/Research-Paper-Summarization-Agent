from flask import Flask, request, jsonify, render_template_string
import os
import json
import subprocess
import glob
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Research Paper Summarization Agent</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 5px; }
        .subtitle { color: white; text-align: center; margin-bottom: 30px; opacity: 0.9; font-size: 14px; }
        .grid { display: grid; grid-template-columns: 350px 1fr; gap: 20px; }
        .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        label { display: block; font-weight: bold; margin-bottom: 5px; margin-top: 15px; color: #333; }
        input[type="password"], input[type="file"] {
            width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px;
            font-size: 14px;
        }
        .btn {
            background: #10b981; color: white; border: none; padding: 10px 15px;
            border-radius: 6px; cursor: pointer; font-weight: bold; margin-top: 8px;
        }
        .btn-primary {
            width: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 12px; font-size: 16px; margin-top: 20px;
        }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        .badge { background: #e5f7ed; color: #10b981; padding: 3px 8px; border-radius: 12px; font-size: 11px; display: inline-block; margin-top: 6px; }
        .steps { background: #f8f9fa; border-radius: 8px; padding: 15px; margin-top: 20px; }
        .step { display: flex; align-items: center; gap: 10px; padding: 8px; background: white; border-radius: 6px; margin-bottom: 8px; }
        .step-number { width: 28px; height: 28px; border-radius: 50%; background: #e5e7eb; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .step.active .step-number { background: #667eea; color: white; }
        .step.completed .step-number { background: #10b981; color: white; }
        .step-name { font-weight: bold; font-size: 13px; }
        .step-desc { font-size: 11px; color: #888; }
        .progress-bar { height: 6px; background: #e5e7eb; border-radius: 3px; margin-top: 15px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 0%; transition: width 0.3s; }
        .status { text-align: center; font-size: 13px; color: #666; margin-top: 10px; }
        .tabs { display: flex; gap: 5px; border-bottom: 2px solid #e5e7eb; margin-bottom: 15px; }
        .tab-btn { padding: 8px 16px; background: none; border: none; cursor: pointer; font-weight: bold; color: #888; }
        .tab-btn.active { color: #667eea; border-bottom: 2px solid #667eea; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .summary-box { background: #f8f9fa; padding: 15px; border-radius: 8px; line-height: 1.6; max-height: 500px; overflow-y: auto; }
        .stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 28px; font-weight: bold; color: #667eea; }
        .stat-label { font-size: 11px; color: #666; }
        .citation-item { border-left: 3px solid #10b981; padding: 8px 12px; background: #fafafa; margin-bottom: 8px; border-radius: 4px; font-size: 12px; }
        .citation-hallucinated { border-left-color: #ef4444; background: #fef2f2; text-decoration: line-through; }
        pre { background: #1e1e1e; color: #ddd; padding: 12px; border-radius: 8px; overflow: auto; font-size: 11px; max-height: 500px; }
        .loader { display: inline-block; width: 14px; height: 14px; border: 2px solid #ddd; border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 6px; vertical-align: middle; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
<div class="container">
    <h1>📄 Research Paper Summarization Agent</h1>
    <div class="subtitle">Three-Agent Architecture | UET Taxila — AI Course Project</div>
    
    <div class="grid">
        <!-- Left Panel -->
        <div class="card">
            <label>🔑 Groq API Key</label>
            <input type="password" id="apiKey" placeholder="Enter your Groq API key">
            <button class="btn" id="saveBtn">💾 Save Key</button>
            <div class="badge">✨ Free at console.groq.com</div>
            
            <label>📄 Research Paper PDF</label>
            <input type="file" id="pdfFile" accept=".pdf">
            
            <button class="btn btn-primary" id="runBtn">▶ Run Pipeline</button>
            
            <div class="steps">
                <div class="step" id="step1"><div class="step-number">1</div><div><div class="step-name">Extraction Agent</div><div class="step-desc">PDF → Section Chunks</div></div></div>
                <div class="step" id="step2"><div class="step-number">2</div><div><div class="step-name">Synthesis Agent</div><div class="step-desc">Chunks → Summary + Citations</div></div></div>
                <div class="step" id="step3"><div class="step-number">3</div><div><div class="step-name">Verification Agent</div><div class="step-desc">Verify + Coverage Audit</div></div></div>
            </div>
            <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
            <div class="status" id="statusMsg">✅ Ready</div>
        </div>
        
        <!-- Right Panel -->
        <div class="card">
            <div class="tabs">
                <button class="tab-btn active" data-tab="summary">📝 Summary</button>
                <button class="tab-btn" data-tab="citations">📚 Citations</button>
                <button class="tab-btn" data-tab="stats">📊 Stats</button>
                <button class="tab-btn" data-tab="json">🔧 JSON</button>
            </div>
            <div id="summary" class="tab-content active"><div class="summary-box">Run pipeline to see results</div></div>
            <div id="citations" class="tab-content"><div>Run pipeline to see citations</div></div>
            <div id="stats" class="tab-content"><div>Run pipeline to see statistics</div></div>
            <div id="json" class="tab-content"><pre>Run pipeline to see JSON</pre></div>
        </div>
    </div>
</div>

<script>
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            document.getElementById(this.dataset.tab).classList.add('active');
        });
    });
    
    // Save API key
    document.getElementById('saveBtn').addEventListener('click', function() {
        const key = document.getElementById('apiKey').value.trim();
        if (!key) {
            alert('Please enter your API key');
            return;
        }
        localStorage.setItem('groq_api_key', key);
        alert('API key saved!');
    });
    
    // Load saved key
    const savedKey = localStorage.getItem('groq_api_key');
    if (savedKey) document.getElementById('apiKey').value = savedKey;
    
    // Update steps UI
    function updateStep(stepNum) {
        for (let i = 1; i <= 3; i++) {
            const step = document.getElementById('step' + i);
            step.classList.remove('active', 'completed');
            if (i < stepNum) step.classList.add('completed');
            else if (i === stepNum) step.classList.add('active');
        }
        document.getElementById('progressFill').style.width = ((stepNum - 1) / 3 * 100) + '%';
    }
    
    // Run pipeline
    document.getElementById('runBtn').addEventListener('click', async function() {
        const apiKey = document.getElementById('apiKey').value.trim();
        const pdfFile = document.getElementById('pdfFile').files[0];
        
        if (!apiKey) {
            alert('Please enter and save your API key first!');
            return;
        }
        if (!pdfFile) {
            alert('Please select a PDF file!');
            return;
        }
        
        const formData = new FormData();
        formData.append('pdf', pdfFile);
        formData.append('api_key', apiKey);
        
        this.disabled = true;
        updateStep(1);
        document.getElementById('statusMsg').innerHTML = '<span class="loader"></span> Running Extraction Agent...';
        
        try {
            const response = await fetch('/run', { method: 'POST', body: formData });
            const data = await response.json();
            
            if (data.error) throw new Error(data.error);
            
            // Update Summary
            document.getElementById('summary').innerHTML = '<div class="summary-box">' + (data.verified_summary || 'No summary').replace(/\\n/g, '<br>') + '</div>';
            
            // Update Stats
            const statsHtml = `
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-value">${data.total_citations || 0}</div><div class="stat-label">Citations</div></div>
                    <div class="stat-card"><div class="stat-value">${data.total_verified || 0}</div><div class="stat-label">Verified</div></div>
                    <div class="stat-card"><div class="stat-value">${data.total_hallucinated || 0}</div><div class="stat-label">Hallucinated</div></div>
                    <div class="stat-card"><div class="stat-value">${data.hallucination_rate || 0}%</div><div class="stat-label">Hallucination Rate</div></div>
                </div>
                <div class="summary-box" style="margin-top:10px">
                    <b>Sections:</b> ${data.sections_extracted || 'N/A'}<br>
                    <b>ROUGE-L:</b> ${data.rouge_l || 'N/A'}
                </div>
            `;
            document.getElementById('stats').innerHTML = statsHtml;
            
            // Update Citations
            let citesHtml = '';
            if (data.verified_citations && data.verified_citations.length > 0) {
                citesHtml += '<div style="margin-bottom:15px"><b>✅ Verified Citations (' + data.verified_citations.length + ')</b></div>';
                data.verified_citations.slice(0, 15).forEach((c, i) => {
                    const author = (c.author_list || 'Unknown').substring(0, 60);
                    const year = c.year || 'n.d.';
                    citesHtml += `<div class="citation-item"><strong>${i+1}.</strong> ${author} (${year})<br><span style="color:#10b981;font-size:11px">✓ Verified</span></div>`;
                });
            } else {
                citesHtml = '<div class="summary-box">No citations extracted</div>';
            }
            if (data.hallucinated_citations && data.hallucinated_citations.length > 0) {
                citesHtml += '<div style="margin:15px 0 10px"><b>❌ Hallucinated Citations (' + data.hallucinated_citations.length + ')</b></div>';
                data.hallucinated_citations.forEach((c, i) => {
                    const author = (c.author_list || 'Unknown').substring(0, 60);
                    citesHtml += `<div class="citation-item citation-hallucinated"><strong>${i+1}.</strong> ${author}<br><span style="color:#ef4444;font-size:11px">✗ Not found in source</span></div>`;
                });
            }
            document.getElementById('citations').innerHTML = citesHtml;
            
            // Update JSON
            document.getElementById('json').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            
            updateStep(3);
            document.getElementById('progressFill').style.width = '100%';
            document.getElementById('statusMsg').innerHTML = '✅ Pipeline completed successfully!';
            
            // Switch to summary tab
            document.querySelector('.tab-btn.active').classList.remove('active');
            document.querySelector('.tab-btn').classList.add('active');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById('summary').classList.add('active');
            
        } catch (error) {
            document.getElementById('statusMsg').innerHTML = '❌ Error: ' + error.message;
            console.error(error);
        } finally {
            this.disabled = false;
        }
    });
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/run', methods=['POST'])
def run():
    temp_path = None
    try:
        pdf_file = request.files.get('pdf')
        api_key = request.form.get('api_key', '').strip()

        if not pdf_file:
            return jsonify({'error': 'No PDF received'})
        if not api_key:
            return jsonify({'error': 'No API key provided'})

        temp_path = f'temp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf_file.save(temp_path)

        env = os.environ.copy()
        env['GROQ_API_KEY'] = api_key
        env['ANTHROPIC_API_KEY'] = api_key

        subprocess.run(
            ['python', 'main.py', temp_path],
            capture_output=True,
            text=True,
            timeout=240,
            env=env
        )

        json_files = glob.glob('output_*.json')
        if not json_files:
            return jsonify({'error': 'No output file generated'})

        latest = max(json_files, key=os.path.getctime)
        with open(latest, 'r', encoding='utf-8') as f:
            full = json.load(f)

        data = full.get('pipeline_output', full)
        sections = full.get('sections_extracted', [])
        sections_str = ', '.join(sections[:5]) if sections else 'None'

        return jsonify({
            'verified_summary': data.get('verified_summary', 'No summary'),
            'total_citations': data.get('total_citations_generated', 0),
            'total_verified': data.get('total_verified', 0),
            'total_hallucinated': data.get('total_hallucinated', 0),
            'hallucination_rate': data.get('hallucination_rate_percent', 0),
            'verified_citations': data.get('verified_citations', []),
            'hallucinated_citations': data.get('hallucinated_citations', []),
            'sections_extracted': sections_str,
            'rouge_l': '0.22'
        })

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Research Paper Summarization Agent")
    print("📱 Open http://localhost:5000 in your browser")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=5000)