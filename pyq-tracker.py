import os
import json
from flask import Flask, render_template_string, request, jsonify

# ====================================================================================
# 1. FLASK BACKEND SETUP (No Changes to Logic)
# ====================================================================================

app = Flask(__name__)

# --- Configuration for Storage ---
storage_dir = '/storage/emulated/0/progress'
FILE_PATH = os.path.join(storage_dir, 'pyq_topics.txt')

# --- Helper Functions for File Operations ---
def read_papers_from_file():
    if not os.path.exists(FILE_PATH): 
        return []
    
    papers = []
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            current_paper_code = None
            current_topics = []
            
            for line in f:
                line = line.strip()
                if not line: continue

                if line.startswith("[PAPER:"):
                    if current_paper_code is not None:
                        papers.append({'code': current_paper_code, 'topics': current_topics})
                    
                    current_paper_code = line.split(":", 1)[1].replace("]", "").strip()
                    current_topics = []
                    continue
                
                parts = line.split('::')
                if len(parts) >= 2:
                    name = parts[0]
                    status = parts[1]
                    revisions = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                    links = parts[3] if len(parts) > 3 else ""
                    
                    current_topics.append({
                        'id': len(current_topics), 
                        'name': name, 
                        'completed': status == 'completed',
                        'revisions': revisions,
                        'links': links
                    })
            
            if current_paper_code is not None:
                papers.append({'code': current_paper_code, 'topics': current_topics})
                
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
        
    return papers

def write_papers_to_file(papers):
    os.makedirs(storage_dir, exist_ok=True)
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        for paper in papers:
            f.write(f"[PAPER: {paper['code']}]\n")
            for topic in paper['topics']:
                status = 'completed' if topic.get('completed') else 'not_completed'
                rev_count = topic.get('revisions', 0)
                links = topic.get('links', '')
                f.write(f"{topic['name']}::{status}::{rev_count}::{links}\n")

# --- API Routes ---

@app.route('/api/papers', methods=['GET'])
def get_papers():
    return jsonify(read_papers_from_file())

@app.route('/api/papers', methods=['POST'])
def add_paper():
    data = request.json
    code = data.get('code', '').strip()
    if not code: return jsonify({'error': 'Code required'}), 400
    
    papers = read_papers_from_file()
    papers.append({'code': code, 'topics': []})
    write_papers_to_file(papers)
    return jsonify({'code': code}), 201

@app.route('/api/topics', methods=['POST'])
def add_topic():
    data = request.json
    paper_code = data.get('paper_code', '').strip()
    name = data.get('name', '').strip()
    links = data.get('links', '').strip()
    
    papers = read_papers_from_file()
    found = False
    
    for paper in papers:
        if paper['code'] == paper_code:
            new_topic = {
                'id': len(paper['topics']),
                'name': name,
                'completed': False,
                'revisions': 0,
                'links': links
            }
            paper['topics'].append(new_topic)
            found = True
            break
            
    if found:
        write_papers_to_file(papers)
        return jsonify({'success': True}), 201
    return jsonify({'error': 'Paper not found'}), 404

@app.route('/api/topics', methods=['PUT'])
def update_topic():
    data = request.json
    paper_code = data.get('paper_code').strip()
    topic_id = int(data.get('topic_id'))
    
    papers = read_papers_from_file()
    for paper in papers:
        if paper['code'] == paper_code:
            if 0 <= topic_id < len(paper['topics']):
                topic = paper['topics'][topic_id]
                action = data.get('action')
                
                if action == 'toggle_status':
                    topic['completed'] = not topic['completed']
                elif action == 'increment_revision':
                    topic['revisions'] += 1
                elif action == 'edit_full':
                    topic['name'] = data.get('name', topic['name'])
                    topic['revisions'] = int(data.get('revisions', topic['revisions']))
                    topic['links'] = data.get('links', topic['links'])
                
                write_papers_to_file(papers)
                return jsonify(topic)
    
    return jsonify({'error': 'Topic not found'}), 404

@app.route('/api/topics', methods=['DELETE'])
def delete_topic():
    data = request.json
    paper_code = data.get('paper_code').strip()
    topic_id = int(data.get('topic_id'))
    
    papers = read_papers_from_file()
    for paper in papers:
        if paper['code'] == paper_code:
            if 0 <= topic_id < len(paper['topics']):
                paper['topics'].pop(topic_id)
                updated_topics = [{'id': i, **{k:v for k,v in t.items() if k != 'id'}} for i, t in enumerate(paper['topics'])]
                paper['topics'] = updated_topics
                write_papers_to_file(papers)
                return jsonify({'success': True})
    return jsonify({'error': 'Topic not found'}), 404

@app.route('/api/papers', methods=['DELETE'])
def delete_paper():
    data = request.json
    code = data.get('code').strip()
    papers = read_papers_from_file()
    papers = [p for p in papers if p['code'] != code]
    write_papers_to_file(papers)
    return jsonify({'success': True})

# ====================================================================================
# 2. FRONTEND (HTML, CSS, JAVASCRIPT) - FANTASTIC UI
# ====================================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PYQ Ultimate Tracker</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --bg-deep: #020617;
            --glass-bg: rgba(15, 23, 42, 0.6);
            --glass-border: rgba(255, 255, 255, 0.1);
            --primary: #06b6d4; /* Cyan Neon */
            --secondary: #ec4899; /* Pink Neon */
            --success: #10b981;
            --text-main: #e2e8f0;
            --text-glow: 0 0 10px rgba(6, 182, 212, 0.5);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background-color: var(--bg-deep);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(6, 182, 212, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(236, 72, 153, 0.15) 0%, transparent 40%);
            color: var(--text-main);
            font-family: 'Rajdhani', sans-serif;
            padding: 20px;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* --- Global Header --- */
        .main-header {
            text-align: center;
            margin-bottom: 40px;
            position: relative;
        }
        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 3rem;
            text-transform: uppercase;
            letter-spacing: 4px;
            background: linear-gradient(90deg, #fff, var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
            animation: glowPulse 3s infinite alternate;
        }

        /* --- Create Paper Section --- */
        .create-section {
            display: flex;
            gap: 15px;
            margin-bottom: 40px;
            background: var(--glass-bg);
            padding: 25px;
            border-radius: 16px;
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }

        input {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--glass-border);
            color: var(--text-main);
            padding: 15px 20px;
            border-radius: 8px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.1rem;
            outline: none;
            transition: 0.3s;
        }
        input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.3);
        }

        .btn-main {
            background: linear-gradient(135deg, var(--primary), #0891b2);
            color: #000;
            font-weight: 800;
            border: none;
            padding: 0 30px;
            border-radius: 8px;
            font-family: 'Orbitron', sans-serif;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: 0.3s;
        }
        .btn-main:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 20px var(--primary);
        }

        /* --- Paper Block (The Glass Cards) --- */
        .paper-block {
            margin-bottom: 50px;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            overflow: hidden;
            backdrop-filter: blur(16px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.4);
            transition: transform 0.3s, border-color 0.3s;
            animation: slideInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
            opacity: 0;
        }
        .paper-block:hover {
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-5px);
        }

        /* --- Paper Header --- */
        .paper-header {
            background: linear-gradient(90deg, rgba(6, 182, 212, 0.1), rgba(236, 72, 153, 0.1));
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--glass-border);
        }
        .paper-title {
            font-family: 'Orbitron', sans-serif;
            color: var(--primary);
            font-size: 1.5rem;
            text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
        }

        /* --- Add Topic Row --- */
        .add-row {
            padding: 20px 30px;
            display: grid;
            grid-template-columns: 2fr 2fr 1fr;
            gap: 15px;
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid var(--glass-border);
        }
        .btn-add {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
            border: 1px solid var(--glass-border);
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 1px;
        }
        .btn-add:hover {
            background: var(--text-main);
            color: #000;
            box-shadow: 0 0 15px white;
        }

        /* --- Horizontal Table --- */
        .table-wrapper {
            width: 100%;
            overflow-x: auto;
            padding: 10px 0;
        }
        /* Custom Scrollbar */
        .table-wrapper::-webkit-scrollbar { height: 6px; }
        .table-wrapper::-webkit-scrollbar-track { background: #000; }
        .table-wrapper::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 3px; }

        .topic-table {
            display: grid;
            grid-template-columns: 250px 140px 100px 280px 120px;
            min-width: 900px;
        }

        .table-row { display: contents; }
        
        .header-cell, .data-cell {
            padding: 18px 15px;
            border-right: 1px solid rgba(255,255,255,0.03);
            display: flex;
            align-items: center;
            font-size: 1rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: background 0.3s;
        }
        .data-cell:hover { background: rgba(255,255,255,0.02); }

        .header-cell {
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            color: rgba(255,255,255,0.4);
            letter-spacing: 2px;
            justify-content: center;
            border-bottom: 2px solid rgba(255,255,255,0.05);
        }
        .header-cell:first-child { justify-content: flex-start; padding-left: 30px; }
        .header-cell:last-child { border-right: none; }

        /* --- Topic Name & Neon Red Line --- */
        .data-cell:first-child { padding-left: 30px; font-weight: 600; font-size: 1.1rem; }
        .red-line {
            position: absolute; top: 50%; left: 0; width: 100%; height: 3px;
            background: var(--secondary);
            box-shadow: 0 0 10px var(--secondary), 0 0 20px var(--secondary);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1);
            pointer-events: none;
            z-index: 5;
        }
        .row-done .data-cell:first-child { color: rgba(255,255,255,0.2); }
        .row-done .red-line { transform: scaleX(1); }

        /* --- Status Badge --- */
        .status-badge {
            width: 100%; padding: 8px; text-align: center;
            border-radius: 4px; font-size: 0.8rem; font-weight: 800;
            cursor: pointer; text-transform: uppercase; letter-spacing: 1px;
            border: 1px solid var(--glass-border);
            transition: 0.3s;
            font-family: 'Orbitron', sans-serif;
        }
        .status-pending { background: rgba(255,255,255,0.05); color: #64748b; }
        .status-completed { 
            background: rgba(16, 185, 129, 0.2); 
            color: var(--success); 
            border-color: var(--success); 
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.2); 
        }

        /* --- Revision Circle --- */
        .rev-circle {
            width: 40px; height: 40px; border-radius: 50%;
            background: rgba(6, 182, 212, 0.1);
            border: 2px solid var(--primary);
            color: var(--primary);
            display: grid; place-items: center; font-weight: bold; cursor: pointer;
            margin: 0 auto; box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
            transition: 0.3s;
        }
        .rev-circle:hover { transform: rotate(90deg) scale(1.1); box-shadow: 0 0 20px var(--primary); }

        /* --- Links --- */
        .link-pill {
            background: rgba(236, 72, 153, 0.1);
            color: var(--secondary);
            padding: 4px 10px; border-radius: 20px;
            font-size: 0.8rem; text-decoration: none;
            border: 1px solid rgba(236, 72, 153, 0.3);
            margin-right: 5px; transition: 0.3s;
        }
        .link-pill:hover { background: var(--secondary); color: #fff; box-shadow: 0 0 10px var(--secondary); }

        /* --- Actions --- */
        .action-cell { justify-content: center; gap: 15px; }
        .icon-btn { background: none; border: none; cursor: pointer; font-size: 1.2rem; transition: 0.3s; opacity: 0.7; }
        .icon-btn:hover { opacity: 1; transform: scale(1.2); }
        .btn-del-paper { background: transparent; border: 1px solid var(--secondary); color: var(--secondary); padding: 5px 15px; cursor: pointer; font-family: 'Orbitron'; font-size: 0.8rem; transition: 0.3s; }
        .btn-del-paper:hover { background: var(--secondary); color: white; box-shadow: 0 0 15px var(--secondary); }

        /* --- Animations --- */
        .thumbs-up {
            position: fixed; top: 50%; left: 50%;
            font-size: 0; pointer-events: none; z-index: 9999;
            animation: popUpRotate 1.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
        }

        @keyframes slideInUp { from { opacity: 0; transform: translateY(50px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes glowPulse { from { text-shadow: 0 0 10px rgba(6, 182, 212, 0.3); } to { text-shadow: 0 0 25px rgba(6, 182, 212, 0.7); } }
        @keyframes popUpRotate {
            0% { transform: translate(-50%, -50%) scale(0.5) rotate(-20deg); opacity: 0; }
            40% { transform: translate(-50%, -50%) scale(2.5) rotate(10deg); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(6) rotate(0deg); opacity: 0; }
        }

        /* --- Modal --- */
        .modal {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); backdrop-filter: blur(5px); z-index: 1000;
            justify-content: center; align-items: center;
        }
        .modal-content {
            background: #0f172a; padding: 30px; border-radius: 16px; width: 90%; max-width: 450px;
            border: 1px solid var(--primary); box-shadow: 0 0 30px rgba(6, 182, 212, 0.2);
        }
        .modal-input { width: 100%; margin-bottom: 15px; padding: 12px; background: #1e293b; border: 1px solid #334155; color: white; border-radius: 6px; }
        .modal-btns { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
        .btn-save { background: var(--primary); color: #000; font-weight: bold; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; }

    </style>
</head>
<body>

    <div class="main-header">
        <h1>PYQ Tracker</h1>
    </div>

    <!-- Create Paper -->
    <div class="create-section">
        <input type="text" id="new-paper-code" placeholder="Enter Question Paper Code (e.g. CS 2024)" autocomplete="off">
        <button class="btn-main" onclick="addPaper()">Initialize Paper</button>
    </div>

    <div id="papers-list"></div>

    <!-- Edit Modal -->
    <div class="modal" id="edit-modal">
        <div class="modal-content">
            <h3 style="color:white; margin-bottom:20px; font-family:'Orbitron'">Edit Module</h3>
            <label style="color:var(--primary); font-size:0.8rem">TOPIC NAME</label>
            <input type="text" id="edit-name" class="modal-input">
            <label style="color:var(--primary); font-size:0.8rem">REVISION CYCLES</label>
            <input type="number" id="edit-rev" class="modal-input">
            <label style="color:var(--primary); font-size:0.8rem">RESOURCE LINKS</label>
            <input type="text" id="edit-links" class="modal-input">
            <div class="modal-btns">
                <button class="btn-del-paper" onclick="closeModal()">Cancel</button>
                <button class="btn-save" onclick="saveEdit()">Update System</button>
            </div>
        </div>
    </div>

    <script>
        let currentEditData = { paper: null, id: null };

        const triggerThumbsUp = () => {
            const el = document.createElement('div');
            el.innerText = '👍';
            el.className = 'thumbs-up';
            document.body.appendChild(el);
            setTimeout(() => el.remove(), 1500);
        };

        const render = async () => {
            const res = await fetch('/api/papers');
            const papers = await res.json();
            const list = document.getElementById('papers-list');
            list.innerHTML = '';

            papers.forEach((paper, index) => {
                const block = document.createElement('div');
                block.className = 'paper-block';
                block.style.animationDelay = `${index * 0.1}s`; // Staggered Animation
                block.dataset.paperCode = paper.code;

                let rowsHtml = '';
                paper.topics.forEach((topic, tIndex) => {
                    const doneClass = topic.completed ? 'row-done' : '';
                    const statusClass = topic.completed ? 'status-completed' : 'status-pending';
                    const statusText = topic.completed ? 'ACQUIRED' : 'PENDING';
                    
                    let linksHtml = '';
                    if(topic.links) {
                        topic.links.split(',').forEach(u => {
                            if(u.trim()) linksHtml += `<a href="${u.trim().startsWith('http')?u.trim():'https://'+u.trim()}" target="_blank" class="link-pill">LINK</a>`;
                        });
                    }

                    rowsHtml += `
                        <div class="table-row ${doneClass}" data-paper="${paper.code}" data-id="${topic.id}">
                            <div class="data-cell" style="position:relative">
                                ${topic.name}
                                <div class="red-line"></div>
                            </div>
                            <div class="data-cell" style="justify-content:center">
                                <div class="status-badge ${statusClass}">${statusText}</div>
                            </div>
                            <div class="data-cell">
                                <div class="rev-circle">#${topic.revisions}</div>
                            </div>
                            <div class="data-cell">${linksHtml || '<span style="color:#333">NO DATA</span>'}</div>
                            <div class="data-cell action-cell">
                                <button class="icon-btn" style="color:var(--primary)">✎</button>
                                <button class="icon-btn" style="color:var(--secondary)">✕</button>
                            </div>
                        </div>
                    `;
                });

                block.innerHTML = `
                    <div class="paper-header">
                        <span class="paper-title">[CODE: ${paper.code}]</span>
                        <button class="btn-del-paper" onclick="deletePaper('${paper.code}')">TERMINATE</button>
                    </div>
                    <div class="add-row">
                        <input type="text" class="topic-input" placeholder="Topic Identifier">
                        <input type="text" class="link-input" placeholder="Reference Links">
                        <button class="btn-add" onclick="handleAddTopic(event)">+</button>
                    </div>
                    <div class="table-wrapper">
                        <div class="topic-table">
                            <div class="header-cell">MODULE</div>
                            <div class="header-cell">STATUS</div>
                            <div class="header-cell">CYCLES</div>
                            <div class="header-cell">DATA LINKS</div>
                            <div class="header-cell">OP</div>
                            ${rowsHtml}
                        </div>
                    </div>
                `;
                list.appendChild(block);
            });
        };

        const addPaper = async () => {
            const codeInput = document.getElementById('new-paper-code');
            const code = codeInput.value.trim();
            if(!code) return;
            await fetch('/api/papers', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ code })
            });
            codeInput.value = '';
            render();
        };

        window.deletePaper = async (code) => {
            if(confirm('Terminate Paper Protocol?')) {
                await fetch('/api/papers', {
                    method: 'DELETE',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code })
                });
                render();
            }
        };

        window.handleAddTopic = async (e) => {
            const block = e.target.closest('.paper-block');
            const paperCode = block.dataset.paperCode;
            const name = block.querySelector('.topic-input').value.trim();
            const links = block.querySelector('.link-input').value.trim();
            if(!name) return;
            
            await fetch('/api/topics', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ paper_code: paperCode, name, links })
            });
            render();
        };

        document.addEventListener('click', async (e) => {
            const row = e.target.closest('.table-row');
            if (!row) return;
            
            const paperCode = row.dataset.paper;
            const topicId = parseInt(row.dataset.id);

            if (e.target.closest('.status-badge')) {
                const isCompleting = !row.classList.contains('row-done');
                if (isCompleting) triggerThumbsUp();

                await fetch('/api/topics', {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ paper_code: paperCode, topic_id: topicId, action: 'toggle_status' })
                });
                render();
            }

            if (e.target.closest('.rev-circle')) {
                await fetch('/api/topics', {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ paper_code: paperCode, topic_id: topicId, action: 'increment_revision' })
                });
                render();
            }

            if (e.target.closest('.icon-btn:last-child')) {
                if(confirm('Delete Module?')) {
                    await fetch('/api/topics', {
                        method: 'DELETE',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ paper_code: paperCode, topic_id: topicId })
                    });
                    render();
                }
            }

            if (e.target.closest('.icon-btn:first-child')) {
                const res = await fetch('/api/papers');
                const papers = await res.json();
                const paper = papers.find(p => p.code === paperCode);
                const topic = paper.topics.find(t => t.id === topicId);

                document.getElementById('edit-name').value = topic.name;
                document.getElementById('edit-rev').value = topic.revisions;
                document.getElementById('edit-links').value = topic.links;
                
                currentEditData = { paper: paperCode, id: topicId };
                document.getElementById('edit-modal').style.display = 'flex';
            }
        });

        window.closeModal = () => document.getElementById('edit-modal').style.display = 'none';

        window.saveEdit = async () => {
            const { paper, id } = currentEditData;
            const name = document.getElementById('edit-name').value;
            const rev = document.getElementById('edit-rev').value;
            const links = document.getElementById('edit-links').value;

            await fetch('/api/topics', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ paper_code: paper, topic_id: id, action: 'edit_full', name, revisions: rev, links })
            });
            closeModal();
            render();
        };

        render();
    </script>
</body>
</html>
"""

# ====================================================================================
# 3. MAIN FLASK ROUTE AND RUNNER
# ====================================================================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
