"""Import user-provided Nido references. Reads ZIP data only; never executes artifact scripts."""
import argparse,hashlib,json,pathlib,re,shutil,zipfile
parser=argparse.ArgumentParser();parser.add_argument('--downloads',type=pathlib.Path,default=pathlib.Path.home()/'Downloads');parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
ROOT=pathlib.Path(__file__).resolve().parents[1]
CACHE=ROOT/'node_modules/.cache'
OUT=ROOT/'public/assembly';OUT.mkdir(parents=True,exist_ok=True)
files=[args.downloads/name for name in ['Ensamble C.U.T.Y (Copy).zip','C.U.T.Y V17 Nido (Copy).zip','CUTY_V17_Nido_rev.zip']]
def sha(data):return hashlib.sha256(data).hexdigest()
manifest={'archives':[{'name':p.name,'sha256':sha(p.read_bytes())}for p in files],'geometrySource':'CUTY_V17_Nido_rev.zip / CUTY_V17_Nido/CUTY_V17.glb','optimization':'gltfpack 1.3.0 -kn -km -vp 16 -vn 12 -cc; no simplification requested','images':[]}
with zipfile.ZipFile(files[0])as z:
 for e in z.infolist():
  if re.fullmatch(r'img3d/[a-z_]+\.webp',e.filename):
   dest=OUT/pathlib.Path(e.filename).name;data=z.read(e);dest.write_bytes(data);manifest['images'].append({'name':dest.name,'sha256':sha(data)})
with zipfile.ZipFile(files[1])as z:
 (OUT/'poster.jpg').write_bytes(z.read('img/poster.jpg'))
 # Preserve original static facial resources as references, not live face replacements.
 for name in ['happy','idle','listening','surprised']:
  (OUT/f'face-{name}.png').write_bytes(z.read(f'tex/cara_{name}.png'))
with zipfile.ZipFile(files[2])as z:
 prefix='CUTY_V17_Nido/'
 for source,target in [('LEEME.md','source-readme.md'),('partes.json','print-parts.json'),('verificacion.json','author-cad-verification.json')]:
  (OUT/target).write_bytes(z.read(prefix+source))
 manifest['sourceGlbSha256']=sha(z.read(prefix+'CUTY_V17.glb'))
 native=CACHE/'cuty-nido-revision/CUTY_V17_Nido';native.mkdir(parents=True,exist_ok=True);(native/'CUTY_V17.glb').write_bytes(z.read(prefix+'CUTY_V17.glb'))
 with zipfile.ZipFile(OUT/'nido-print-stl.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as output:
  for e in z.infolist():
   if e.filename.startswith(prefix+'STL_imprimir/')and e.filename.endswith('.stl'):
    info=zipfile.ZipInfo('STL_imprimir/'+pathlib.Path(e.filename).name,date_time=(2026,11,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;output.writestr(info,z.read(e))
if args.prepare:
 print('Prepared native model and supplied reference assets; run gltfpack before final import.');raise SystemExit(0)
optimized=CACHE/'cuty-nido-revision/nido-web.glb'
shutil.copyfile(optimized,ROOT/'public/models/cuty.glb')
manifest['webGlbSha256']=sha(optimized.read_bytes());manifest['webGlbBytes']=optimized.stat().st_size
# Native metadata is retained without claiming physical validation.
manifest['limitations']=['Purchased electronics are simplified mechanical solids.','CAD verification is an author-supplied report, not rerun or physical validation.','Fuse pad coordinates differ from current repository KiCad by 3.4 mm in Y.','No authored skeletal rig or animation clips; visual pivots are runtime simulations.']
(OUT/'provenance.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
print('Imported',len(manifest['images']),'assembly images; optimized GLB',manifest['webGlbBytes'],'bytes')
