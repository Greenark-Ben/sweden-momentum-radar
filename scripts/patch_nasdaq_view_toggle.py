from pathlib import Path

PAGE = Path('nasdaq.html')
html = PAGE.read_text(encoding='utf-8')

# Replace the old pseudo-element control with a real, accessible two-button segmented control.
controls_end = '</select></div>\n\n    <div class="tablewrap" id="radar-table">'
replacement = '''</select><div class="view-toggle" role="group" aria-label="Visningsläge">
  <button type="button" class="view-btn active" id="viewTable" aria-pressed="true"><span aria-hidden="true">▥</span> Tabell</button>
  <button type="button" class="view-btn" id="viewCompact" aria-pressed="false"><span aria-hidden="true">▦</span> Kompakt</button>
</div></div>

    <div class="tablewrap" id="radar-table">'''
if 'class="view-toggle"' not in html:
    if controls_end not in html:
        raise SystemExit('Could not locate NASDAQ controls block')
    html = html.replace(controls_end, replacement, 1)

CSS = r'''
/* ===== Real NASDAQ table/compact segmented control ===== */
.controls:after{display:none!important;content:none!important}
.view-toggle{height:44px;display:grid;grid-template-columns:1fr 1fr;border:1px solid #e4e2db;border-radius:9px;overflow:hidden;background:#f7f7f4;min-width:0;width:100%}
.view-btn{appearance:none;border:0;background:transparent;color:#454d49;font:inherit;font-size:11px;font-weight:650;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;transition:background .15s ease,color .15s ease,box-shadow .15s ease;min-width:0;padding:0 14px}
.view-btn+ .view-btn{border-left:1px solid #e6e4dd}
.view-btn.active{background:#175f34;color:#fff;box-shadow:inset 0 0 0 1px rgba(0,0,0,.03)}
.view-btn:focus-visible{outline:2px solid #1d7a3d;outline-offset:-3px;position:relative;z-index:2}
.view-btn span{font-size:13px;line-height:1}
.tablewrap.compact-mode th,.tablewrap.compact-mode td{padding-top:8px!important;padding-bottom:8px!important}
.tablewrap.compact-mode th:nth-child(5),.tablewrap.compact-mode td:nth-child(5),
.tablewrap.compact-mode th:nth-child(8),.tablewrap.compact-mode td:nth-child(8),
.tablewrap.compact-mode th:nth-child(11),.tablewrap.compact-mode td:nth-child(11),
.tablewrap.compact-mode th:nth-child(12),.tablewrap.compact-mode td:nth-child(12){display:none!important}
.tablewrap.compact-mode .name{display:none!important}
.tablewrap.compact-mode .up{padding-bottom:10px!important}
.tablewrap.compact-mode .up:after{display:none!important}
@media(max-width:1050px){.view-toggle{display:grid!important;width:100%!important}}
'''
if 'Real NASDAQ table/compact segmented control' not in html:
    html = html.replace('</style>', CSS + '\n</style>', 1)

JS = r'''
<script id="nasdaq-view-toggle-script">
(()=>{
  const wrap=document.getElementById('radar-table');
  const tableBtn=document.getElementById('viewTable');
  const compactBtn=document.getElementById('viewCompact');
  if(!wrap||!tableBtn||!compactBtn)return;
  const setMode=(compact)=>{
    wrap.classList.toggle('compact-mode',compact);
    tableBtn.classList.toggle('active',!compact);
    compactBtn.classList.toggle('active',compact);
    tableBtn.setAttribute('aria-pressed',String(!compact));
    compactBtn.setAttribute('aria-pressed',String(compact));
    try{localStorage.setItem('nasdaqViewMode',compact?'compact':'table')}catch(e){}
  };
  tableBtn.addEventListener('click',()=>setMode(false));
  compactBtn.addEventListener('click',()=>setMode(true));
  let saved='table';try{saved=localStorage.getItem('nasdaqViewMode')||'table'}catch(e){}
  setMode(saved==='compact');
})();
</script>
'''
if 'nasdaq-view-toggle-script' not in html:
    html = html.replace('</body>', JS + '\n</body>', 1)

PAGE.write_text(html,encoding='utf-8')
print('Real NASDAQ table/compact toggle applied')
