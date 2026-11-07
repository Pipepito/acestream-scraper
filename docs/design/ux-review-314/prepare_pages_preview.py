"""Prepare static design previews over a pinned, preserved Pages snapshot.
No network/publication. Requires an empty output directory.
Use --site-ref <current-gh-pages-sha> --site-prefix . --design-ref <design-sha>.
The optional --site-prefix docs supports a reviewed main/docs baseline, but does
not authorize replacing independently changed current Pages files.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,io,json,re,shutil,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[3]
DESIGN='docs/design/ux-review-314'
PREVIEW='design/ux-review-314'
FILES=['index.html','workflow-gallery.html','workflow-prototype.html','workflow-engine.js','workflow-data.js','workflow-prototype.css','presentation-presets.css','admin-prototype.html','admin-prototype.css','prototype.html']
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def extract(ref,paths,prefix,dest):
 count=0
 with tarfile.open(fileobj=io.BytesIO(git('archive','--format=tar',ref,*paths)),mode='r:') as archive:
  for member in archive.getmembers():
   name=PurePosixPath(member.name)
   if name.is_absolute() or '..' in name.parts:raise ValueError('Unsafe path')
   if member.isdir():continue
   if not member.isfile():raise ValueError('Non-regular archive member: '+str(name))
   target=dest.joinpath(*name.relative_to(prefix).parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.extractfile(member).read());count+=1
 return count
def hashes(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--site-ref',required=True);ap.add_argument('--site-prefix',choices=['.','docs'],default='.');ap.add_argument('--design-ref',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output.resolve()
 if out.exists() and any(out.iterdir()):ap.error('Output must be empty')
 site=git('rev-parse',a.site_ref+'^{commit}').decode().strip();design=git('rev-parse',a.design_ref+'^{commit}').decode().strip();out.mkdir(parents=True,exist_ok=True)
 extract(site,[] if a.site_prefix=='.' else ['docs'],a.site_prefix,out)
 original={k:v for k,v in hashes(out).items() if not k.startswith(PREVIEW+'/')}
 preview=out/PREVIEW
 if preview.exists():shutil.rmtree(preview) # Only the copied preview inside this newly created empty staging output.
 count=extract(design,[DESIGN+'/'+f for f in FILES]+[DESIGN+'/assets',DESIGN+'/workflow-exports'],DESIGN,preview)
 source=f'https://github.com/Pipepito/acestream-scraper/blob/{design}/{DESIGN}/'
 for path in [*preview.glob('*.html'),preview/'workflow-engine.js']:
  text=re.sub(r'href="([\w-]+\.md)',lambda m:'href="'+source+m[1],path.read_text());path.write_text(text)
 # Historical illustrative concept is retained behind an explicit historical link.
 old=preview/'prototype.html';text=old.read_text()
 if 'Content-Security-Policy' not in text:
  text=text.replace('<head>', '<head><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'self\' \'unsafe-inline\'; script-src \'self\' \'unsafe-inline\'; font-src \'self\'; img-src \'self\' data:; connect-src \'none\'; media-src \'none\'; frame-src \'none\'; object-src \'none\'; form-action \'none\'; base-uri \'none\'">',1)
 old.write_text(text)
 final=hashes(out);changed=[k for k,v in original.items() if final.get(k)!=v]
 if changed:raise ValueError('Existing Pages content changed: '+str(changed))
 manifest=dict(site_source=site,site_prefix=a.site_prefix,design_source=design,preserved_site_files=len(original),copied_design_files=count,existing_site_changes=changed,sha256=final)
 (preview/'publication-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in manifest.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
