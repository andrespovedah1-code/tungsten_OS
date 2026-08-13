import fs from 'node:fs';
import vm from 'node:vm';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const index=fs.readFileSync('index.html','utf8');
let patch=fs.readFileSync('demo-core-patches.js','utf8');
if(patch.includes('demo-targeted-2026-08-12-r2')){
  patch=patch.replace(/\\\\\\"/g,'\\"').replace('demo-targeted-2026-08-12-r2','demo-targeted-2026-08-12-r2-hotfix1');
}
const sandbox={console}; sandbox.globalThis=sandbox; sandbox.window=sandbox;
vm.runInNewContext(patch,sandbox,{filename:'demo-core-patches.normalized.js'});
if(typeof sandbox.__TUNGSTEN_APPLY_DEMO_PATCHES!=='function') throw new Error('Patch transformer missing');
const transformed=sandbox.__TUNGSTEN_APPLY_DEMO_PATCHES(index);
const scripts=[...transformed.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(m=>m[1]);
if(!scripts.length) throw new Error('No inline scripts found in transformed app');
let failed=false;
for(let i=0;i<scripts.length;i++){
  const file=path.join(os.tmpdir(),`tungsten-generated-${i}.js`);
  fs.writeFileSync(file,scripts[i]);
  const r=spawnSync(process.execPath,['--check',file],{encoding:'utf8'});
  if(r.status!==0){
    failed=true;
    console.error(`GENERATED_SCRIPT_${i}_SYNTAX_FAIL`);
    console.error(r.stderr||r.stdout);
  } else console.log(`GENERATED_SCRIPT_${i}_SYNTAX_OK`);
}
if(failed) process.exit(1);
console.log('R2_GENERATED_APP_SYNTAX_OK');
