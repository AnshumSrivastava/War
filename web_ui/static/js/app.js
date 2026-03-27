// Core State
const state = {
    camera: { x: 0, y: 0, zoom: 50 },
    tool: 'cursor',
    side: 'Attacker',
    entities: [],
    hoveredHex: null,
    isDragging: false,
    lastMouse: { x: 0, y: 0 }
};

// Canvas Setup
const canvas = document.getElementById('hexCanvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;
    render();
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// Hex Math utility
const HexMath = {
    hexToPixel: (q, r, size) => {
        const x = size * (3/2 * q);
        const y = size * (Math.sqrt(3)/2 * q + Math.sqrt(3) * r);
        return {x, y};
    },
    pixelToHex: (x, y, size) => {
        const q = (2./3 * x) / size;
        const r = (-1./3 * x + Math.sqrt(3)/3 * y) / size;
        return HexMath.hexRound(q, r, -q-r);
    },
    hexRound: (q, r, s) => {
        let rq = Math.round(q);
        let rr = Math.round(r);
        let rs = Math.round(s);
        const q_diff = Math.abs(rq - q);
        const r_diff = Math.abs(rr - r);
        const s_diff = Math.abs(rs - s);
        
        if (q_diff > r_diff && q_diff > s_diff) rq = -rr - rs;
        else if (r_diff > s_diff) rr = -rq - rs;
        else rs = -rq - rr;
        return {q: rq, r: rr, s: rs};
    },
    getCorners: (x, y, size) => {
        const corners = [];
        for (let i = 0; i < 6; i++) {
            const angle_deg = 60 * i;
            const angle_rad = Math.PI / 180 * angle_deg;
            corners.push({
                x: x + size * Math.cos(angle_rad),
                y: y + size * Math.sin(angle_rad)
            });
        }
        return corners;
    }
};

// Interaction
canvas.addEventListener('mousedown', (e) => {
    if (e.button === 1 || (e.button === 0 && state.tool === 'cursor')) {
        state.isDragging = true;
    }
    state.lastMouse = {x: e.clientX, y: e.clientY};
});

window.addEventListener('mouseup', () => {
    state.isDragging = false;
});

canvas.addEventListener('mousemove', (e) => {
    if (state.isDragging) {
        const dx = e.clientX - state.lastMouse.x;
        const dy = e.clientY - state.lastMouse.y;
        state.camera.x -= dx;
        state.camera.y -= dy;
        render();
    }
    state.lastMouse = {x: e.clientX, y: e.clientY};
    
    // Hover logic
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left + state.camera.x - canvas.width/2;
    const y = e.clientY - rect.top + state.camera.y - canvas.height/2;
    const hex = HexMath.pixelToHex(x, y, state.camera.zoom);
    
    // Avoid re-rendering if hover hex matches
    if (!state.hoveredHex || hex.q !== state.hoveredHex.q || hex.r !== state.hoveredHex.r) {
        state.hoveredHex = hex;
        render();
    }
});

canvas.addEventListener('wheel', (e) => {
    const zoomBase = 1.1;
    if (e.deltaY < 0) state.camera.zoom *= zoomBase;
    else state.camera.zoom /= zoomBase;
    state.camera.zoom = Math.max(10, Math.min(150, state.camera.zoom));
    render();
});

canvas.addEventListener('click', (e) => {
    if (state.isDragging) return; // don't click if just finished panning
    
    if (state.tool === 'place_agent' && state.hoveredHex) {
        placeAgent(state.hoveredHex);
    }
});

// APIs
function placeAgent(hex) {
    fetch('/api/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            type: 'place_agent',
            q: hex.q,
            r: hex.r,
            side: document.querySelector('input[name="side"]:checked').value
        })
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            state.entities.push(data.agent);
            
            // UI Feedback micro animation
            const el = document.createElement('div');
            el.innerHTML = '<i class="fa-solid fa-check"></i>';
            el.style.position = 'fixed';
            el.style.left = state.lastMouse.x + 'px';
            el.style.top = state.lastMouse.y + 'px';
            el.style.color = '#10b981';
            el.style.pointerEvents = 'none';
            el.style.transition = 'all 1s ease-out';
            document.body.appendChild(el);
            setTimeout(() => {
                el.style.transform = 'translateY(-30px) scale(2)';
                el.style.opacity = '0';
            }, 10);
            setTimeout(() => el.remove(), 1000);
            
            render();
        }
    });
}

// Rendering
function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    
    // Draw infinite grid view
    const drawRadius = Math.ceil(Math.max(canvas.width, canvas.height) / (state.camera.zoom * 1.5)) + 1;
    const centerHex = HexMath.pixelToHex(state.camera.x - cx, state.camera.y - cy, state.camera.zoom);
    
    ctx.lineWidth = 1;
    
    for (let q = centerHex.q - drawRadius; q <= centerHex.q + drawRadius; q++) {
        for (let r = centerHex.r - drawRadius; r <= centerHex.r + drawRadius; r++) {
            const hex = {q, r, s: -q-r};
            // approximate distance
            if (Math.abs(q - centerHex.q) + Math.abs(r - centerHex.r) + Math.abs(hex.s - centerHex.s) > 2 * drawRadius) continue;
            
            drawHex(ctx, hex, cx, cy);
        }
    }
    
    // Draw entities
    state.entities.forEach(ent => {
        const {x, y} = HexMath.hexToPixel(ent.q, ent.r, state.camera.zoom);
        const {sx, sy} = screenCoords(x, y, cx, cy);
        
        ctx.beginPath();
        ctx.arc(sx, sy, state.camera.zoom * 0.6, 0, Math.PI*2);
        ctx.fillStyle = ent.side === 'Attacker' ? '#ef4444' : '#3b82f6';
        ctx.fill();
        ctx.strokeStyle = '#09090b';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        ctx.fillStyle = '#fff';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(ent.side[0], sx, sy+3);
    });
    
    // Hover highlight
    if (state.hoveredHex) {
        const {x, y} = HexMath.hexToPixel(state.hoveredHex.q, state.hoveredHex.r, state.camera.zoom);
        const {sx, sy} = screenCoords(x, y, cx, cy);
        const corners = HexMath.getCorners(sx, sy, state.camera.zoom - 1);
        
        ctx.beginPath();
        ctx.moveTo(corners[0].x, corners[0].y);
        for(let i=1; i<6; i++) ctx.lineTo(corners[i].x, corners[i].y);
        ctx.closePath();
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.fill();
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

function screenCoords(wx, wy, cx, cy) {
    return {
        sx: wx - state.camera.x + cx,
        sy: wy - state.camera.y + cy
    };
}

function drawHex(ctx, hex, cx, cy) {
    const {x, y} = HexMath.hexToPixel(hex.q, hex.r, state.camera.zoom);
    const {sx, sy} = screenCoords(x, y, cx, cy);
    
    const corners = HexMath.getCorners(sx, sy, state.camera.zoom - 1);
    
    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    for(let i=1; i<6; i++) ctx.lineTo(corners[i].x, corners[i].y);
    ctx.closePath();
    
    ctx.fillStyle = 'rgba(24, 24, 27, 0.2)';
    ctx.fill();
    ctx.strokeStyle = '#3f3f46';
    ctx.lineWidth = 1;
    ctx.stroke();
}

// UI Setup
document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.tool = btn.dataset.tool;
        
        const deploySettings = document.getElementById('deploySettings');
        if (state.tool === 'place_agent') {
            deploySettings.style.display = 'block';
            setTimeout(() => {
                deploySettings.style.opacity = '1';
                deploySettings.style.transform = 'translateY(0)';
            }, 10);
        } else {
            deploySettings.style.opacity = '0';
            deploySettings.style.transform = 'translateY(-10px)';
            setTimeout(() => deploySettings.style.display = 'none', 300);
        }
        
        if (state.tool === 'place_agent') canvas.style.cursor = 'crosshair';
        else if (state.tool === 'cursor') canvas.style.cursor = 'default';
        else canvas.style.cursor = 'crosshair';
    });
});

document.getElementById('btnZoomIn').addEventListener('click', () => {
    state.camera.zoom *= 1.2; render();
});
document.getElementById('btnZoomOut').addEventListener('click', () => {
    state.camera.zoom /= 1.2; render();
});
document.getElementById('btnResetCam').addEventListener('click', () => {
    state.camera.x = 0; state.camera.y = 0; state.camera.zoom = 50; render();
});

// Load init state
fetch('/api/state').then(r=>r.json()).then(data => {
    if(data.entities) state.entities = data.entities;
    render();
});
