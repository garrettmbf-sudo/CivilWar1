"""Editable counter layout production; generated art and approved portraits stay separate."""
from pathlib import Path
import base64, hashlib, json, math, shutil, textwrap
from xml.sax.saxutils import escape
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
ROSTER = '''Stonewall Brigade|BG Richard B. Garnett|Infantry|2nd, 4th, 5th, 27th, 33rd Virginia|17,23|2|mdl_CSA_RGarnett.png
Fulkerson’s Brigade|Col. Samuel V. Fulkerson|Infantry|23rd, 37th Virginia|15,23|2|
Burks’ Brigade|Col. Jesse S. Burks|Infantry|21st, 42nd, 48th Virginia, 1st VA Bn|17,20|0|
Ashby’s Cavalry|Col. Turner Ashby|Light Cavalry|7th Virginia Cavalry|27,17|0|mdl_CSA_TAshby.png
Chew’s Horse Artillery|Capt. R. Preston Chew|Artillery|3 guns (horse battery)|26,17|0|
Rockbridge Artillery|Capt. William T. Poague|Artillery|4 guns|16,21|0|
Carpenter’s Battery|Capt. Joseph Carpenter|Artillery|Alleghany Battery, 4 guns|18,21|0|
Caskie’s Battery|Capt. William H. Caskie|Artillery|Hampden Artillery, 4 guns|15,22|0|
Wooding’s Battery|Capt. George W. Wooding|Artillery|Danville Artillery, 4 guns|20,21|0|
Pleasants’ Battery|Capt. James Pleasants|Artillery|2 guns|20,20|0|
1st Brigade (Kimball)|Col. Nathan Kimball|Infantry|14th IN, 8th OH, 67th OH, 84th PA|25,26|0|mdl_USA_NKimball.png
2nd Brigade (Sullivan)|Col. Jeremiah C. Sullivan|Infantry|39th IL, 13th IN, 5th OH, 62nd OH|29,24|0|mdl_USA_JCSullivan.png
3rd Brigade (Tyler)|Col. Erastus B. Tyler|Infantry|7th IN, 7th OH, 29th OH, 110th PA, 1st WV|17,25|0|mdl_USA_EBTyler.png
Battery A WV Artillery|Capt. John Jenks|Artillery|6 guns|25,27|0|
Battery B WV Artillery|(unknown)|Artillery|6 guns|27,27|0|
Battery E 4th US Artillery|Lt. Joseph C. Clark Jr.|Artillery|Regular Army, 6 guns|26,26|0|
Battery L 1st OH Artillery|Capt. James M. Robinson|Artillery|6 guns|26,25|0|
Brodhead’s Cavalry|Col. Thornton F. Brodhead|Light Cavalry|Detachments: MI, PA, MD, WV, OH cavalry|13,25|0|'''

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uri(p): return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
def text(x,y,label,size=40,color='#f7eed8',family='Arial',weight='bold',anchor='middle'):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(label)}</text>'

def main():
    SOURCE.mkdir(exist_ok=True, parents=True)
    sheet = SOURCE / 'formation_sheet.png'
    sw,sh = Image.open(sheet).size
    records=[]
    for i,line in enumerate(ROSTER.splitlines()):
        name,commander,kind,composition,pos,entrench,portrait=line.split('|')
        available_portrait=portrait or None
        # User direction: portraits belong only on division / army headquarters.
        # This roster contains no such headquarters, so all 18 use formation art.
        portrait=''
        country='Confederacy' if i<10 else 'Union'
        color='#793733' if i<10 else '#1d425b'
        row={'index':i+1,'name':name,'commander':commander,'type':kind,'composition':composition,
             'grid_pos':[int(v) for v in pos.split(',')],'entrenchment':int(entrench),'portrait':None,
             'available_portrait_not_used':available_portrait,
             'country':country,'filename':name+'.png','install_path':f'MODS/First Kernstown 1862/Graphics/Units/{country}/{name}.png'}
        # The user-supplied Name is the filename; the engine's matching unit Name must agree.
        pieces=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1024" height="1024" viewBox="0 0 1024 1024">',
                '<defs><clipPath id="card"><rect x="64" y="64" width="896" height="896" rx="12"/></clipPath></defs>',
                '<g clip-path="url(#card)"><rect x="64" y="64" width="896" height="896" fill="#eee4cc"/>',
                f'<rect x="64" y="64" width="896" height="152" fill="{color}"/>',
                f'<rect x="64" y="768" width="896" height="192" fill="{color}"/>']
        title=name.upper().replace(' (KIMBALL)','').replace(' (SULLIVAN)','').replace(' (TYLER)','')
        title_lines=textwrap.wrap(title,25,break_long_words=False)
        for j,t in enumerate(title_lines): pieces.append(text(512,125+j*54,t,47 if len(t)<23 else 40))
        panel_row={'Infantry':0,'Artillery':1,'Light Cavalry':2}[kind]
        # Illustration rows have no gutters; exclude the next row's first pixels.
        panel_top,panel_bottom=[(0,333),(344,662),(670,1024)][panel_row]
        panel_y=panel_top*sh/1024
        panel_height=(panel_bottom-panel_top)*sh/1024
        col=0 if i<10 else 1
        left=310 if portrait else 100
        # Nested SVG viewBox selects the authored atlas panel without modifying source bytes.
        pieces.append(f'<svg x="{left}" y="240" width="{920-left}" height="500" viewBox="{col*sw/2} {panel_y} {sw/2} {panel_height}" preserveAspectRatio="xMidYMid meet"><defs><clipPath id="art"><rect x="{col*sw/2}" y="{panel_y}" width="{sw/2}" height="{panel_height}"/></clipPath></defs><image clip-path="url(#art)" width="{sw}" height="{sh}" xlink:href="{uri(sheet)}"/></svg>')
        if portrait:
            original=ROOT.parent/'portraits'/portrait
            copy=SOURCE/portrait
            if not copy.exists(): shutil.copy2(original,copy)
            assert digest(original)==digest(copy)
            pw,ph=Image.open(copy).size
            scale=.94/math.sqrt((pw/276)**2+(ph/368)**2)
            w,h=pw*scale,ph*scale
            pieces.append(f'<ellipse cx="215" cy="496" rx="138" ry="184" fill="#eee4cc" stroke="{color}" stroke-width="9"/>')
            pieces.append(f'<image x="{215-w/2}" y="{496-h/2}" width="{w}" height="{h}" xlink:href="{uri(copy)}"/>')
            row['portrait_sha256']=digest(original)
        short=commander.replace('BG ','').replace('Col. ','').replace('Capt. ','').replace('Lt. ','')
        surname=short.split()[-1].upper() if short!='(unknown)' else 'COMMANDER UNCONFIRMED'
        if surname=='JR.': surname='CLARK JR.'
        pieces.append(text(512,848,surname,74 if len(surname)<14 else 38,family='Georgia'))
        pieces.append(text(512,904,commander if short!='(unknown)' else 'Identity not supplied',31))
        pieces.append('</g><rect x="68" y="68" width="888" height="888" rx="9" fill="none" stroke="#baa473" stroke-width="8"/>')
        pieces.append('</svg>')
        folder=ROOT/'masters'/country;folder.mkdir(parents=True,exist_ok=True)
        (folder/(name+'.svg')).write_text('\n'.join(pieces),encoding='utf-8')
        records.append(row)
    (ROOT/'roster_manifest.json').write_text(json.dumps({'date':'1862-03-23','roster_authority':'User-supplied production list; not an independent historical certification','units':records},indent=2,ensure_ascii=False),encoding='utf-8')
    print('Created 18 editable SVG masters; portraits reserved for division / army HQ.')

if __name__=='__main__': main()
