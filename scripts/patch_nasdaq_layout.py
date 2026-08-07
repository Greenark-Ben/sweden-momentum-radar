from pathlib import Path

PAGE = Path('nasdaq.html')
html = PAGE.read_text(encoding='utf-8')

CSS = r'''
/* ===== NASDAQ approved reference layout v2 ===== */
body{overflow-x:hidden!important}
.shell{max-width:1540px!important;margin-left:198px!important;padding:0 30px 22px!important}
.reference-sidebar{width:198px!important}
.appbar{max-width:1280px;margin:0 auto!important}
.hero{max-width:1280px;margin:28px auto 20px!important;grid-template-columns:minmax(360px,.92fr) minmax(600px,1.55fr)!important;gap:28px!important}
.hero h1{font-size:32px!important;line-height:1.08!important;white-space:normal!important}
.hero .sub{max-width:430px!important}
.grid{grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:12px!important}
.kpi{min-width:0!important;min-height:128px!important;padding:22px 14px 16px 65px!important}
.kpi:before{left:16px!important;top:21px!important;width:36px!important;height:36px!important}
.controls{max-width:1280px;margin:20px auto 15px!important;grid-template-columns:minmax(260px,1.55fr) minmax(145px,.75fr) minmax(145px,.78fr) minmax(145px,.78fr) 230px!important;gap:10px!important;padding:14px!important;align-items:center!important}
.controls input,.controls select{min-width:0!important;width:100%!important}
.controls:after{height:44px!important;min-width:0!important;width:230px!important;justify-self:end!important;background:linear-gradient(90deg,#0d5b31 0 50%,#f7f7f4 50% 100%)!important;color:#fff!important;border:1px solid #e7e5de!important;box-shadow:none!important;border-radius:8px!important;font-weight:700!important;letter-spacing:0!important}
.tablewrap{max-width:1280px;margin:0 auto!important}
table{table-layout:auto!important;width:100%!important}
th,td{white-space:nowrap!important}
th:nth-child(2),td:nth-child(2){min-width:180px!important;white-space:normal!important}
th:nth-child(3),td:nth-child(3){min-width:125px!important}
th:nth-child(9),td:nth-child(9){min-width:120px!important}
th:nth-child(12),td:nth-child(12){min-width:110px!important}
.note,.footer{max-width:1280px;margin-left:auto!important;margin-right:auto!important}
.sidebar-nav a{font-size:12.5px!important;padding:13px 15px!important;gap:12px!important}
.sidebar-nav a[href="index.html"]:before{content:"🇸🇪";font-size:15px}.sidebar-nav a[href="nasdaq.html"]:before{content:"🇺🇸";font-size:15px}.sidebar-nav a[href="index.html"] .nav-ico,.sidebar-nav a[href="nasdaq.html"] .nav-ico{display:none!important}
@media(max-width:1320px){
  .shell{margin-left:176px!important;padding-left:18px!important;padding-right:18px!important}.reference-sidebar{width:176px!important}
  .hero{grid-template-columns:1fr!important}.grid{grid-template-columns:repeat(4,minmax(145px,1fr))!important}
  .controls{grid-template-columns:minmax(250px,1.4fr) repeat(3,minmax(135px,.8fr)) 210px!important}.controls:after{width:210px!important}
}
@media(max-width:1050px){
  .grid{grid-template-columns:repeat(2,1fr)!important}.controls{grid-template-columns:1fr 1fr!important}.controls:after{display:none!important}.tablewrap{overflow:auto!important}table{min-width:1100px!important}
}
@media(max-width:760px){
 .shell{margin-left:0!important;padding:0 12px 20px!important}.hero{margin-top:18px!important}.grid{grid-template-columns:1fr 1fr!important}.controls{grid-template-columns:1fr!important}
}
'''

if 'NASDAQ approved reference layout v2' not in html:
    html = html.replace('</style>', CSS + '\n</style>', 1)

# Match the approved NASDAQ page copy more closely.
html = html.replace('NASDAQ Momentum Radar</h1>', 'Top 50 NASDAQ Momentum Aktier</h1>', 1)
html = html.replace('US LARGE-CAP EQUITIES INTELLIGENCE', 'HIGH VELOCITY MARKET INTELLIGENCE', 1)
html = html.replace('NASDAQ Top 50</span>', 'NASDAQ Top 50</span>')

PAGE.write_text(html, encoding='utf-8')
print('NASDAQ approved reference layout applied')
