DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DATAMINE-HUB | SWARM_CORE</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        :root {
            --bg: #000000;
            --panel-bg: #000000;
            --border: 3px solid #1a1a1a;
            --border-highlight: 3px solid #333333;
            --text-main: #ffffff;
            --text-dim: #666666;
            --accent: #00ff41; 
            --danger: #ff0000;
        }

        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Courier New', Courier, monospace;
            max-width: 800px; /* Reduced from 1000px */
            margin: 0 auto;
            padding: 48px 16px; /* Reduced from 60px 20px */
            line-height: 1.3;
            font-weight: 900;
        }

        h1, h2 { 
            color: var(--text-main); 
            text-transform: uppercase; 
            letter-spacing: 3px; 
            margin: 0;
        }
        
        h1 { font-size: 2rem; border-left: 8px solid var(--accent); padding-left: 16px; margin-bottom: 8px; }
        p.subtext { font-size: 0.75rem; color: var(--accent); margin-bottom: 32px; text-transform: uppercase; }

        .stats-container { display: flex; gap: 16px; margin-bottom: 32px; }
        .stat-box { 
            flex: 1; 
            border: var(--border); 
            padding: 20px; /* Reduced from 25px */
            text-align: left; 
            background: var(--panel-bg);
            position: relative;
        }
        .stat-box::after {
            content: "";
            position: absolute;
            top: 4px; right: 4px;
            width: 8px; height: 8px;
            background: var(--accent);
        }
        .stat-value { font-size: 1.6rem; font-weight: 900; display: block; color: var(--text-main); margin-bottom: 4px; }
        .stat-label { font-size: 0.6rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1.5px; }

        #network-canvas {
            height: 400px; /* Reduced from 500px */
            border: var(--border-highlight);
            margin-bottom: 32px;
            background-color: #000;
        }

        .section-header { 
            background: #111;
            padding: 12px 16px; 
            margin-bottom: 0; 
            border: var(--border);
            border-bottom: none;
        }
        
        .list-container { 
            height: 280px; /* Reduced from 350px */
            overflow-y: auto; 
            border: var(--border); 
            padding: 16px; 
            background: var(--panel-bg); 
            margin-bottom: 32px; 
            scrollbar-width: thin;
            scrollbar-color: #333 #000;
        }
        .list-item { 
            margin-bottom: 16px; 
            font-size: 0.8rem; /* Scaled down */
            border-bottom: 1px solid #1a1a1a; 
            padding-bottom: 12px;
        }
        .list-item:last-child { border-bottom: none; }
        .tag { color: var(--accent); font-weight: 900; margin-right: 8px; }
        .dim { color: var(--text-dim); font-size: 0.7rem; }

        .admin-panel { border: 3px solid var(--danger); padding: 24px; background: #000; margin-top: 48px; }
        .admin-panel h2 { font-size: 1rem; margin-bottom: 16px; }
        .admin-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        
        input, select, button { 
            background: #000; 
            border: 2px solid #333; 
            color: #fff; 
            padding: 12px; 
            font-family: inherit; 
            font-weight: 900;
            text-transform: uppercase;
            font-size: 0.75rem;
        }
        button { 
            background: var(--danger); 
            color: #000; 
            border: none; 
            cursor: pointer; 
            grid-column: span 2;
            letter-spacing: 2px;
        }
        button:hover { background: #ff3333; }
        input:focus { border-color: var(--accent); outline: none; }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 0; }
    </style>
</head>
<body>
    <h1>DATAMINE-HUB</h1>
    <p id="connection-status" class="subtext">// SYSTEM_READY // SWARM_LINK_PENDING</p>

    <div class="stats-container">
        <div class="stat-box">
            <span id="agents-count" class="stat-value">00</span>
            <span class="stat-label">Agents_Online</span>
        </div>
        <div class="stat-box">
            <span id="datasets-count" class="stat-value">00</span>
            <span class="stat-label">Data_Nodes_Total</span>
        </div>
        <div class="stat-box">
            <span id="posts-count" class="stat-value">00</span>
            <span class="stat-label">Board_Uplinks</span>
        </div>
    </div>

    <div class="section-header"><h2>Deployment_Control</h2></div>
    <div class="list-container" style="height: auto; margin-bottom: 40px;">
        <div class="admin-grid" style="grid-template-columns: 1fr 1fr 1fr;">
            <input type="text" id="deploy-url" placeholder="TARGET_URL (e.g. https://futo.edu.ng)">
            <select id="deploy-role">
                <option value="scraper">SCRAPER_UNIT</option>
                <option value="cleaner">CLEANER_BOT</option>
                <option value="analyzer">ANALYZER_CORE</option>
            </select>
            <button onclick="deployAgent()" style="grid-column: span 1; background: var(--accent); color: #000;">INITIATE_DEPLOYMENT</button>
        </div>
        <p id="deploy-status" class="dim" style="margin-top: 10px; font-size: 0.7rem;">// READY_FOR_DISPATCH //</p>
    </div>

    <div class="section-header"><h2>Lineage_Explorer</h2></div>
    <div id="network-canvas"></div>

    <div class="section-header"><h2>Recent_Harvests</h2></div>
    <div id="datasets-list" class="list-container"></div>

    <div class="section-header"><h2>Communication_Array</h2></div>
    <div id="posts-list" class="list-container"></div>

    <div class="admin-panel">
        <h2>TERMINAL_BROADCAST_OVERRIDE</h2>
        <form onsubmit="broadcastMessage(event)" class="admin-grid">
            <input type="password" id="admin-key" placeholder="ADMIN_AUTH_TOKEN" required>
            <select id="admin-channel" required>
                <option value="announcements">#ANNOUNCEMENTS</option>
                <option value="scraping-ops">#SCRAPING-OPS</option>
                <option value="system">#SYSTEM_ALERTS</option>
            </select>
            <input type="text" id="admin-message" placeholder="ENTER_MESSAGE_CONTENT..." style="grid-column: span 2;" required>
            <button type="submit">EXECUTE_BROADCAST</button>
        </form>
    </div>

    <script>
        let network = null;
        let ws = null;

        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

            ws.onopen = () => {
                const status = document.getElementById('connection-status');
                status.innerText = '// SWARM_CONNECTION_ESTABLISHED //';
                status.style.color = '#00ff41';
            };

            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'new_dataset') {
                    prependDataset(msg.data);
                    refreshGraph();
                    updateStats();
                } else if (msg.type === 'new_post') {
                    prependPost(msg.data);
                    updateStats();
                }
            };

            ws.onclose = () => {
                const status = document.getElementById('connection-status');
                status.innerText = '// CONNECTION_TERMINATED // RE-LINKING...';
                status.style.color = '#ff0000';
                setTimeout(initWebSocket, 3000);
            };
        }

        async function updateStats() {
            const res = await fetch('/api/admin/stats');
            const stats = await res.json();
            document.getElementById('agents-count').innerText = String(stats.agents || 0).padStart(2, '0');
            document.getElementById('datasets-count').innerText = String(stats.datasets || 0).padStart(2, '0');
            document.getElementById('posts-count').innerText = String(stats.posts || 0).padStart(2, '0');
        }

        function prependDataset(d) {
            const list = document.getElementById('datasets-list');
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `<span class="tag">[NODE_DETECTED]</span> ${d.hash.substring(0,16)}... <br> <span class="dim">ORIGIN: ${d.agent_id.substring(0,12)} | METRICS: ${d.metrics}</span>`;
            list.prepend(item);
        }

        function prependPost(p) {
            const list = document.getElementById('posts-list');
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `<span class="tag">#${p.channel_name.toUpperCase()}</span> <span class="dim">UPLINK_ID:${p.agent_id.substring(0,8)}</span><br>${p.content.toUpperCase()}`;
            list.prepend(item);
        }

        async function fetchInitialData() {
            updateStats();
            const dataRes = await fetch('/api/data/recent');
            const datasets = await dataRes.json();
            datasets.forEach(d => prependDataset(d));
            const postsRes = await fetch('/api/channels/posts');
            const posts = await postsRes.json();
            posts.reverse().forEach(p => prependPost(p));
            refreshGraph();
        }

        async function refreshGraph() {
            const res = await fetch('/api/data/graph');
            const graphData = await res.json();
            const container = document.getElementById('network-canvas');
            const data = {
                nodes: new vis.DataSet(graphData.nodes),
                edges: new vis.DataSet(graphData.edges)
            };
            const options = {
                nodes: {
                    shape: 'square',
                    size: 16,
                    color: { background: '#000', border: '#00ff41', highlight: { background: '#00ff41', border: '#fff' } },
                    font: { color: '#ffffff', face: 'Courier New', size: 10, weight: 'bold' },
                    borderWidth: 2
                },
                edges: {
                    color: '#333333',
                    width: 1.5,
                    arrows: { to: { enabled: true, scaleFactor: 0.6 } }
                },
                physics: { enabled: true, solver: 'barnesHut' }
            };
            if (!network) {
                network = new vis.Network(container, data, options);
            } else {
                network.setData(data);
            }
        }

        async function broadcastMessage(event) {
            if (event) event.preventDefault();
            const key = document.getElementById('admin-key').value;
            const channel = document.getElementById('admin-channel').value;
            const content = document.getElementById('admin-message').value;
            if (!key || !content) return;
            try {
                const res = await fetch(`/api/channels/${channel}/posts`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
                    body: JSON.stringify({ content: content })
                });
                if (res.ok) {
                    document.getElementById('admin-message').value = '';
                } else {
                    const err = await res.json();
                    alert("BROADCAST_FAILED: " + (err.detail || "Unauthorized"));
                }
            } catch (err) {
                console.error(err);
                alert("BROADCAST_ERROR: CONNECTION_INTERRUPTED");
            }
        }

        async function deployAgent() {
            const url = document.getElementById('deploy-url').value;
            const role = document.getElementById('deploy-role').value;
            const status = document.getElementById('deploy-status');
            
            if (!url) { alert("Target URL required"); return; }
            
            status.innerText = "// INITIATING_DISPATCH_PROTOCOL //";
            status.style.color = "var(--accent)";

            try {
                const res = await fetch('/api/jobs/spawn', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ role: role, target_url: url })
                });

                if (res.ok) {
                    const data = await res.json();
                    status.innerText = `// AGENT_DEPLOYED // ID: ${data.agent_id.substring(0,8)} // PID: ${data.pid}`;
                    status.style.color = "var(--accent)";
                    setTimeout(() => {
                        status.innerText = "// READY_FOR_DISPATCH //";
                        status.style.color = "var(--text-dim)";
                    }, 5000);
                    updateStats();
                } else {
                    status.innerText = "// DISPATCH_FAILED //";
                    status.style.color = "var(--danger)";
                }
            } catch (err) {
                console.error(err);
                status.innerText = "// ERROR_IN_PROTOCOL //";
                status.style.color = "var(--danger)";
            }
        }

        initWebSocket();
        fetchInitialData();
    </script>
</body>
</html>
"""
