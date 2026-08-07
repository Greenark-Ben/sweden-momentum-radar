from pathlib import Path

PAGES = [
    (Path('index.html'), 'swedenViewMode'),
    (Path('sweden-large-cap.html'), 'swedenLargeCapViewMode'),
]

CSS = r'''
/* ===== Shared LITHIC Markets UI parity v2 ===== */
body{overflow-x:hidden!important}
.shell{max-width:1540px!important;margin-left:198px!important;padding:0 30px 22px!important}
.reference-sidebar{width:198px!important}
.appbar{max-width:1280px;margin:0 auto!important}
.hero{max-width:1280px;margin:28px auto 20px!important;grid-template-columns:minmax(360px,.92fr) minmax(600px,1.55fr)!important;gap:28px!important}
.hero h1{font-size:32px!important;line-height:1.08!important;white-space:normal!important}.hero .sub{max-width:430px!important}
.grid{grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:12px!important}.kpi{min-width:0!important;min-height:128px!important;padding:22px 14px 16px 65px!important}.kpi:before{left:16px!important;top:21px!important;width:36px!important;height:36px!important}
.controls{max-width:1280px;margin:20px auto 15px!important;grid-template-columns:minmax(260px,1.55fr) minmax(145px,.75fr) minmax(145px,.78fr) minmax(145px,.78fr) 230px!important;gap:10px!important;padding:14px!important;align-items:center!important}.controls input,.controls select{min-width:0!important;width:100%!important}.controls:after{display:none!important;content:none!important}
.view-toggle{height:44px;display:grid;grid-template-columns:1fr 1fr;border:1px solid #e4e2db;border-radius:9px;overflow:hidden;background:#f7f7f4;min-width:0;width:100%}.view-btn{appearance:none;border:0;background:transparent;color:#454d49;font:inherit;font-size:11px;font-weight:650;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;min-width:0;padding:0 12px}.view-btn+.view-btn{border-left:1px solid #e6e4dd}.view-btn.active{background:#175f34;color:#fff}.view-btn:focus-visible{outline:2px solid #1d7a3d;outline-offset:-3px;position:relative;z-index:2}
.tablewrap{max-width:1280px;margin:0 auto!important}table{table-layout:auto!important;width:100%!important}th,td{white-space:nowrap!important}th:nth-child(2),td:nth-child(2){min-width:180px!important;white-space:normal!important}th:nth-child(3),td:nth-child(3){min-width:125px!important}th:nth-child(9),td:nth-child(9){min-width:120px!important}th:nth-child(12),td:nth-child(12){min-width:110px!important}.note,.footer{max-width:1280px;margin-left:auto!important;margin-right:auto!important}
.sidebar-nav a{font-size:12.5px!important;padding:13px 15px!important;gap:12px!important}.sidebar-nav a[href="index.html"]:before{content:"🇸🇪";font-size:15px}.sidebar-nav a[href="sweden-large-cap.html"]:before{content:"🇸🇪";font-size:15px}.sidebar-nav a[href="index.html"] .nav-ico,.sidebar-nav a[href="sweden-large-cap.html"] .nav-ico{display:none!important}
.tablewrap.compact-mode th,.tablewrap.compact-mode td{padding-top:8px!important;padding-bottom:8px!important}.tablewrap.compact-mode th:nth-child(5),.tablewrap.compact-mode td:nth-child(5),.tablewrap.compact-mode th:nth-child(8),.tablewrap.compact-mode td:nth-child(8),.tablewrap.compact-mode th:nth-child(11),.tablewrap.compact-mode td:nth-child(11),.tablewrap.compact-mode th:nth-child(12),.tablewrap.compact-mode td:nth-child(12){display:none!important}.tablewrap.compact-mode .name{display:none!important}.tablewrap.compact-mode .up{padding-bottom:10px!important}.tablewrap.compact-mode .up:after{display:none!important}
@media(max-width:1320px){.shell{margin-left:176px!important;padding-left:18px!important;padding-right:18px!important}.reference-sidebar{width:176px!important}.hero{grid-template-columns:1fr!important}.grid{grid-template-columns:repeat(4,minmax(145px,1fr))!important}.controls{grid-template-columns:minmax(250px,1.4fr) repeat(3,minmax(135px,.8fr)) 210px!important}}
@media(max-width:1050px){.grid{grid-template-columns:repeat(2,1fr)!important}.controls{grid-template-columns:1fr 1fr!important}.view-toggle{display:grid!important;width:100%!important}.tablewrap{overflow:auto!important}table{min-width:1100px!important}}
@media(max-width:760px){.reference-sidebar{display:none!important}.shell{margin-left:0!important;padding:0 12px 20px!important}.hero{margin-top:18px!important}.grid{grid-template-columns:1fr 1fr!important}.controls{grid-template-columns:1fr!important}}
'''

for page, storage_key in PAGES:
    html=page.read_text(encoding='utf-8')
    if 'class="view-toggle"' not in html:
        marker='</select></div>\n\n    <div class="tablewrap" id="radar-table">'
        replacement='''</select><div class="view-toggle" role="group" aria-label="Visningsläge"><button type="button" class="view-btn active" id="viewTable" aria-pressed="true"><span aria-hidden="true">▥</span> Tabell</button><button type="button" class="view-btn" id="viewCompact" aria-pressed="false"><span aria-hidden="true">▦</span> Kompakt</button></div></div>\n\n    <div class="tablewrap" id="radar-table">'''
        if marker not in html: raise SystemExit(f'Could not locate controls block in {page}')
        html=html.replace(marker,replacement,1)
    if 'Shared LITHIC Markets UI parity v2' not in html: html=html.replace('</style>',CSS+'\n</style>',1)
    if 'shared-market-view-toggle-script' not in html:
        js=f'''<script id="shared-market-view-toggle-script">(()=>{{const w=document.getElementById('radar-table'),t=document.getElementById('viewTable'),c=document.getElementById('viewCompact');if(!w||!t||!c)return;const k={storage_key!r};const set=m=>{{w.classList.toggle('compact-mode',m);t.classList.toggle('active',!m);c.classList.toggle('active',m);t.setAttribute('aria-pressed',String(!m));c.setAttribute('aria-pressed',String(m));try{{localStorage.setItem(k,m?'compact':'table')}}catch(e){{}}}};t.addEventListener('click',()=>set(false));c.addEventListener('click',()=>set(true));let s='table';try{{s=localStorage.getItem(k)||'table'}}catch(e){{}}set(s==='compact');}})();</script>'''
        html=html.replace('</body>',js+'\n</body>',1)
    page.write_text(html,encoding='utf-8')
    print(f'Shared Swedish market UI parity applied to {page}')
