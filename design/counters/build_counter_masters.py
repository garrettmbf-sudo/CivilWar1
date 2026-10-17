"""Reproducible native counter artwork; approved portraits are embedded intact."""
from pathlib import Path
import base64, json, math, html
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'design/counters'; SOURCE=D/'source'
STYLES={'A':('Historical Command',128),'B':('Traditional Wargame',112),'C':('Illustrated Formation',116),'D':('Commander Portrait',148),'E':('Formation / Headquarters Hybrid',116)}
PORTRAITS={'GARNETT':'mdl_CSA_RGarnett.png','KIMBALL':'mdl_USA_NKimball.png','TYLER':'mdl_USA_EBTyler.png','SULLIVAN':'mdl_USA_JCSullivan.png','ASHBY':'mdl_CSA_TAshby.png','JACKSON':'mdl_CSA_TJJackson.png'}
def image_tag(file,x,y,w,h):
 data=base64.b64encode((SOURCE/file).read_bytes()).decode()
 return f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>'
def tx(x,y,t,size=13,fill='#f5ecd6',anchor='start',family='Arial',weight='bold'):
 return f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(t)}</text>'
def symbol(kind,x,y,w=29,h=20):
 a=f'<g stroke="#222a29" stroke-width="2.2" fill="none"><rect x="{x}" y="{y}" width="{w}" height="{h}"/>'
 if kind=='INF': a+=f'<path d="M{x},{y}l{w},{h}m0,{-h}l{-w},{h}"/>'
 elif kind=='CAV': a+=f'<path d="M{x},{y+h}l{w},{-h}"/>'
 elif kind=='ART':a+=f'<circle cx="{x+w/2}" cy="{y+h/2}" r="5" fill="#222a29"/>'
 else:a+=f'</g>'+tx(x+w/2,y+15,'HQ',12,'#222a29','middle');return a
 return a+'</g>'
def roster():
 raw=json.loads((ROOT/'data/layers/kernstown_units.json').read_text())['units']
 names=[('GARNETT','STONEWALL'),('FULKERSON','VA BDE'),('BURKS','VA BDE'),('ASHBY','7TH VA CAV'),('CHEW','HORSE ART'),('POAGUE','ROCKBRIDGE'),('CARPENTER','ALLEGHANY'),('CASKIE','HAMPDEN'),('WOODING','DANVILLE'),('PLEASANTS','BATTERY'),('KIMBALL','1ST BDE'),('SULLIVAN','2ND BDE'),('TYLER','3RD BDE'),('JENKS','A / VA ART'),('B / VA','VA BATTERY'),('CLARK','E / 4TH US'),('ROBINSON','L / 1ST OH'),('BRODHEAD','CAVALRY')]
 result=[]
 for i,(r,(name,formation)) in enumerate(zip(raw,names)):
  result.append(dict(id=f'k{i+1:02}',name=name,formation=formation,side='CSA' if r['country']=='Confederacy' else 'USA',kind={'Infantry':'INF','Light Cavalry':'CAV','Napoleon 12pdr':'ART'}[r['template_name']],col=r['col'],row=r['row'],placement='branch deployment',portrait=PORTRAITS.get(name)))
 result += [dict(id='k19',name='JACKSON',formation='VALLEY HQ',side='CSA',kind='HQ',col=20,row=19,placement='stress-test HQ placement only',portrait=PORTRAITS['JACKSON']),dict(id='k20',name='KIMBALL',formation='ACTING HQ',side='USA',kind='HQ',col=27,row=29,placement='stress-test HQ placement only; same officer as 1st Brigade',portrait=PORTRAITS['KIMBALL'])]
 return result

def svg(unit,style,state='normal'):
 name=unit['name']; side=unit['side']; kind=unit['kind']; portrait=unit['portrait']; col='#7b3430' if side=='CSA' else '#204d68'; paper='#eee4ce'; ink='#202a29'; style = ('D' if kind=='HQ' else 'C') if style=='E' else style; height=STYLES[style][1]; top=(160-height)/2; y=top
 a=[f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 160 160"><title>{style}: {html.escape(name)} — {unit["formation"]}</title>',f'<rect x="16" y="{y}" width="128" height="{height}" rx="3" fill="#17201f"/><rect x="18" y="{y+2}" width="124" height="{height-4}" rx="2" fill="{paper}" stroke="#c0a876" stroke-width="1.5"/>']
 # Major type and affiliation remain consistent across all treatments.
 a+=[f'<rect x="19" y="{y+3}" width="122" height="23" fill="{col}"/>',tx(23,y+19,unit['formation'],14),tx(137,y+19,side,9,anchor='end')]
 body_y=y+28; foot=y+height-36
 if style=='A':
  if portrait:a+=[image_tag(portrait,36,body_y,72,foot-body_y)]
  else:a+=[symbol(kind,64,body_y+11,42,30),tx(80,foot-8,'NO PORTRAIT',8,ink,'middle')]
  a += [symbol(kind,25,body_y+5),tx(135,body_y+17,'II' if kind=='INF' else kind,10,ink,'end')]
 elif style=='B':
  if portrait:a += [image_tag(portrait,22,body_y,44,foot-body_y)]
  a += [symbol(kind,78,body_y+5,44,29),tx(100,foot-5,'BDE' if kind=='INF' else kind,9,ink,'middle')]
 elif style=='C':
  asset='Unit_CMN_Arty6lb.png' if kind=='ART' else 'Unit_CSA_Cav1.png' if kind=='CAV' else 'Unit_CSA_Inf1.png' if side=='CSA' else 'Unit_USA_Inf1.png'
  if kind=='INF':
   for sx,sy,sw,sh in [(57,body_y+5,26,foot-body_y-5),(77,body_y+1,29,foot-body_y-1),(100,body_y+6,27,foot-body_y-6)]:a += [image_tag(asset,sx,sy,sw,sh)]
  elif kind!='HQ':a += [image_tag(asset,54,body_y+4,75,foot-body_y-4)]
  if portrait:a += [f'<ellipse cx="41" cy="{body_y+24}" rx="19" ry="24" fill="{paper}" stroke="{col}" stroke-width="2"/>',image_tag(portrait,23,body_y+2,36,44)]
  else:a += [symbol(kind,22,body_y+3)]
 elif style=='D':
  if portrait:a += [image_tag(portrait,37,body_y,90,foot-body_y)]
  else:a += [symbol(kind,55,body_y+20,50,34),tx(80,foot-8,'NO APPROVED PORTRAIT',7,ink,'middle')]
  a += [symbol(kind,23,body_y+3,25,18)]
 a += [f'<rect x="19" y="{foot}" width="122" height="33" fill="{col}"/>',tx(80,foot+18,name,18,'#fff1d7','middle','Georgia'),tx(25,foot+30,'S —',9),tx(135,foot+30,'M —',9,anchor='end')]
 # State marker: redundant shape/letter plus color; no speculative numeric ratings.
 states={'normal':('#c4bc9f','•'),'shaken':('#d9a05c','!'),'fatigued':('#dbb840','F'),'forced':('#77bbdf','»'),'supply':('#83a978','+')}
 c,label=states[state];a += [f'<rect x="129" y="{body_y+27}" width="11" height="15" fill="{c}" stroke="{ink}" stroke-width=".7"/>',tx(134.5,body_y+38,label,11,ink,'middle')]
 a += ['</svg>'];return ''.join(a)

def main():
 for p in ['masters','sprites','previews']: (D/p).mkdir(exist_ok=True,parents=True)
 units=roster();(D/'roster.json').write_text(json.dumps(units,indent=2)+'\n')
 for style in STYLES:
  for u in units:(D/'masters'/f'{style.lower()}_{u["id"]}.svg').write_text(svg(u,style),encoding='utf-8')
 for state in ['normal','shaken','fatigued','forced','supply']:(D/'masters'/f'hybrid_garnett_{state}.svg').write_text(svg(units[0],'E',state),encoding='utf-8')
 print('105 editable SVG masters generated')
if __name__=='__main__': main()

