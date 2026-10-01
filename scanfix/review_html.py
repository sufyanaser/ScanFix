"""Generate a standalone HTML corner editor for ScanFix."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

import numpy as np


def _data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def generate_review_html(
    source_path: Path,
    output_html: Path,
    *,
    corners: np.ndarray | None,
    confidence: float,
    reason: str,
) -> None:
    source_path = Path(source_path)
    output_html = Path(output_html)

    initial_corners = (
        np.asarray(corners, dtype=float).round(2).tolist()
        if corners is not None
        else None
    )

    payload = {
        "sourceName": source_path.name,
        "imageDataUrl": _data_url(source_path),
        "initialCorners": initial_corners,
        "confidence": float(confidence),
        "reason": reason,
    }

    data = json.dumps(payload, ensure_ascii=False)

    html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ScanFix Corner Review</title>
<style>
  :root { color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }
  body { margin:0; background:#0d1117; color:#e6edf3; }
  header { padding:14px 18px; border-bottom:1px solid #30363d; display:flex; gap:16px; align-items:center; flex-wrap:wrap; }
  header strong { font-size:16px; }
  .meta { color:#9da7b3; font-size:13px; }
  main { display:grid; grid-template-columns:minmax(0,1fr) 310px; height:calc(100vh - 58px); }
  .stage { position:relative; overflow:auto; background:#161b22; display:flex; align-items:flex-start; justify-content:center; padding:22px; }
  canvas { max-width:100%; box-shadow:0 8px 40px rgba(0,0,0,.35); cursor:crosshair; }
  aside { border-left:1px solid #30363d; padding:18px; overflow:auto; background:#0d1117; }
  button { width:100%; margin:6px 0; padding:11px 12px; border:1px solid #3b82f6; border-radius:7px; background:#1f6feb; color:white; font-weight:600; cursor:pointer; }
  button.secondary { background:#21262d; border-color:#30363d; }
  pre { white-space:pre-wrap; background:#161b22; padding:10px; border-radius:6px; font-size:12px; }
  .hint { color:#9da7b3; font-size:13px; line-height:1.5; }
  .warn { color:#f2cc60; }
  @media(max-width:850px){main{grid-template-columns:1fr;height:auto} aside{border-left:0;border-top:1px solid #30363d}}
</style>
</head>
<body>
<header>
  <strong>ScanFix Corner Review</strong>
  <span id="file" class="meta"></span>
  <span id="status" class="meta"></span>
</header>
<main>
  <section class="stage"><canvas id="canvas"></canvas></section>
  <aside>
    <p class="hint">Drag the four handles to the physical corners of the document page. The document itself is not edited here.</p>
    <p id="warning" class="hint warn"></p>
    <button id="download">Download review.json</button>
    <button id="reset" class="secondary">Reset suggested corners</button>
    <button id="frame" class="secondary">Use full image frame</button>
    <pre id="coords"></pre>
  </aside>
</main>
<script>
const DATA = __SCANFIX_DATA__;
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const img = new Image();
let points = [];
let initial = null;
let active = -1;
let scale = 1;

document.getElementById("file").textContent = DATA.sourceName;
document.getElementById("status").textContent =
  "reason=" + DATA.reason + "  confidence=" + DATA.confidence.toFixed(3);

if (DATA.reason !== "ok" && DATA.reason !== "segmentation-page" && DATA.reason !== "full-frame-document") {
  document.getElementById("warning").textContent =
    "Automatic detection is uncertain. Confirm all four corners manually.";
}

function fullFrame(){
  return [[0,0],[img.naturalWidth-1,0],[img.naturalWidth-1,img.naturalHeight-1],[0,img.naturalHeight-1]];
}
function normalize(p){ return [Math.round(p[0]*100)/100, Math.round(p[1]*100)/100]; }
function updateCoords(){
  document.getElementById("coords").textContent =
    JSON.stringify({accepted:true,corners:points.map(normalize)}, null, 2);
}
function fitCanvas(){
  const maxW = Math.max(320, document.querySelector(".stage").clientWidth - 50);
  scale = Math.min(1, maxW / img.naturalWidth);
  canvas.width = Math.round(img.naturalWidth * scale);
  canvas.height = Math.round(img.naturalHeight * scale);
  draw();
}
function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.drawImage(img,0,0,canvas.width,canvas.height);
  if(points.length !== 4) return;
  const q = points.map(function(p){ return [p[0]*scale,p[1]*scale]; });
  ctx.lineWidth = Math.max(2,3*scale);
  ctx.strokeStyle = "#22c55e";
  ctx.beginPath();
  ctx.moveTo(q[0][0],q[0][1]);
  for(let i=1;i<4;i++) ctx.lineTo(q[i][0],q[i][1]);
  ctx.closePath();
  ctx.stroke();
  const labels=["TL","TR","BR","BL"];
  q.forEach(function(p,i){
    const x=p[0], y=p[1];
    ctx.fillStyle="#ef4444";
    ctx.beginPath();ctx.arc(x,y,Math.max(7,10*scale),0,Math.PI*2);ctx.fill();
    ctx.fillStyle="#fff";ctx.font="bold 13px Segoe UI";
    ctx.fillText(labels[i],x+12,y-10);
  });
  updateCoords();
}
function pointer(e){
  const r=canvas.getBoundingClientRect();
  return [(e.clientX-r.left)/scale,(e.clientY-r.top)/scale];
}
canvas.addEventListener("pointerdown",function(e){
  const pos=pointer(e), x=pos[0], y=pos[1];
  let best=-1, dist=Infinity;
  points.forEach(function(p,i){
    const d=Math.hypot(p[0]-x,p[1]-y);
    if(d<dist){dist=d;best=i;}
  });
  if(best>=0 && dist < 45/scale){active=best;canvas.setPointerCapture(e.pointerId);}
});
canvas.addEventListener("pointermove",function(e){
  if(active<0)return;
  let pos=pointer(e), x=pos[0], y=pos[1];
  x=Math.max(0,Math.min(img.naturalWidth-1,x));
  y=Math.max(0,Math.min(img.naturalHeight-1,y));
  points[active]=[x,y];draw();
});
canvas.addEventListener("pointerup",function(){active=-1;});
canvas.addEventListener("pointercancel",function(){active=-1;});

document.getElementById("reset").onclick=function(){points=(initial||fullFrame()).map(function(p){return p.slice();});draw();};
document.getElementById("frame").onclick=function(){points=fullFrame();draw();};
document.getElementById("download").onclick=function(){
  const review={accepted:true,source_name:DATA.sourceName,corners:points.map(normalize)};
  const blob=new Blob([JSON.stringify(review,null,2)],{type:"application/json"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download="review.json";
  a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href);},1000);
};

img.onload=function(){
  initial = DATA.initialCorners || fullFrame();
  points=initial.map(function(p){return p.slice();});
  fitCanvas();
};
window.addEventListener("resize",function(){if(img.complete) fitCanvas();});
img.src=DATA.imageDataUrl;
</script>
</body>
</html>'''.replace("__SCANFIX_DATA__", data)

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding="utf-8")
