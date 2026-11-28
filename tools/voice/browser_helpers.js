// 在內建瀏覽器的 huggingface.co 頁面（已登入）執行：產生還沒做好的國語、台語區塊語音
// 用法：先整段貼上執行，再 await VOICE.run()，完成後用 VOICE.chunk(i) 逐段取回
(()=>{
const PAGES='https://chennn231-code.github.io/assistive-device-compass/';
const BZ={host:'https://breezeblue-breeze-tts-2-demo.hf.space',space:'BreezeBlue/breeze-tts-2-demo',fn:4,trig:29};
const TG={host:'https://leon80148-taigi-cosyvoice3-voice-clone.hf.space',space:'leon80148/taigi-cosyvoice3-voice-clone',fn:2,trig:13};
const REFTXT='您好，我會用比較慢的速度，一步一步跟您說明，怎麼申請輔具補助。';
const ORDER=['about','check','warn','flow','calc','all','v3','home','county','dict','history','foreign','news','links'];
const V=window.VOICE={log:[],out:{},CH:[]};
const call=async(S,data)=>{const j=await fetch('/api/spaces/'+S.space+'/jwt?expires_in=180&billing_details=true&encrypted=true').then(r=>r.json());const sh=Math.random().toString(36).slice(2);
  await fetch(S.host+'/gradio_api/queue/join',{method:'POST',headers:{'Content-Type':'application/json','X-ZeroGPU-Token':j.encryptedToken.keyId+':'+j.encryptedToken.encrypted},body:JSON.stringify({data,fn_index:S.fn,session_hash:sh,event_data:null,trigger_id:S.trig})});
  const t=await fetch(S.host+'/gradio_api/queue/data?session_hash='+sh).then(r=>r.text());const m=t.match(/"msg":"process_completed".*?"output":(\{.*\}),"success":(\w+)/);return m?{ok:m[2]==='true',out:JSON.parse(m[1])}:{ok:false,out:{error:t.slice(-300)}}};
const upload=async(S,blob)=>{const fd=new FormData();fd.append('files',new File([blob],'ref.wav',{type:'audio/wav'}));const up=await fetch(S.host+'/gradio_api/upload',{method:'POST',body:fd}).then(r=>r.json());return {path:up[0],meta:{_type:'gradio.FileData'},orig_name:'ref.wav'}};
const wav16=async(url)=>{const ab=await fetch(url).then(r=>r.arrayBuffer());const ac=new AudioContext();const buf=await ac.decodeAudioData(ab);const rate=16000,n=Math.ceil(buf.duration*rate);const oc=new OfflineAudioContext(1,n,rate);const s=oc.createBufferSource();s.buffer=buf;s.connect(oc.destination);s.start();const o=(await oc.startRendering()).getChannelData(0);const dv=new DataView(new ArrayBuffer(44+n*2));const w=(p,x)=>{for(let i=0;i<x.length;i++)dv.setUint8(p+i,x.charCodeAt(i))};w(0,'RIFF');dv.setUint32(4,36+n*2,true);w(8,'WAVE');w(12,'fmt ');dv.setUint32(16,16,true);dv.setUint16(20,1,true);dv.setUint16(22,1,true);dv.setUint32(24,rate,true);dv.setUint32(28,rate*2,true);dv.setUint16(32,2,true);dv.setUint16(34,16,true);w(36,'data');dv.setUint32(40,n*2,true);for(let i=0;i<n;i++)dv.setInt16(44+i*2,Math.max(-1,Math.min(1,o[i]))*32767,true);const b=new Uint8Array(dv.buffer);let bin='';for(let i=0;i<b.length;i+=8192)bin+=String.fromCharCode(...b.subarray(i,i+8192));return btoa(bin)};
const exists=async(l,k)=>(await fetch(PAGES+'audio/'+l+'_'+k+'.mp3',{method:'HEAD',cache:'no-store'})).ok;
V.run=async(max=6)=>{
  if(location.hostname!=='huggingface.co')return 'ERROR: open https://huggingface.co first';
  const who=await fetch('/api/whoami-v2');if(!who.ok)return 'ERROR: not logged in to Hugging Face';
  const S=await fetch(PAGES+'tools/voice/scripts.json',{cache:'no-store'}).then(r=>r.json());
  const ref=await fetch(PAGES+'tools/voice/ref_voice.mp3').then(r=>r.blob());
  const todo=[];for(const k of ORDER){if(!await exists('zh',k))todo.push(['zh',k]);if(!await exists('tw',k))todo.push(['tw',k])}
  V.todo=todo.map(x=>x.join('_'));const refs={};let done=0,stop={zh:false,tw:false};
  for(const [l,k] of todo){if(done>=max)break;if(stop[l])continue;const Sx=l==='zh'?BZ:TG;
    try{refs[l]=refs[l]||await upload(Sx,ref);
      const data=l==='zh'?[S.zh[k],refs[l],REFTXT,42]:[S.tw[k],'custom',refs[l],REFTXT,2026111202];
      const r=await call(Sx,data);
      if(!r.ok){const e=JSON.stringify(r.out).slice(0,200);V.log.push(l+'_'+k+' FAIL '+e);if(/quota/i.test(e))stop[l]=true;continue}
      V.out[l+'_'+k]=await wav16(r.out.data[0].url);done++;V.log.push(l+'_'+k+' OK')}
    catch(e){V.log.push(l+'_'+k+' ERR '+e)}}
  const all=Object.entries(V.out).map(([k,v])=>'VWAV:'+k+':'+v+':END').join('\n');V.CH=[];for(let i=0;i*190000<all.length;i++)V.CH.push(all.slice(i*190000,(i+1)*190000));
  return JSON.stringify({made:Object.keys(V.out),chunks:V.CH.length,remaining:V.todo.length-done,log:V.log})};
V.chunk=i=>'VCH'+i+'<<'+V.CH[i]+'>>'+'~'.repeat(Math.max(0,110000-V.CH[i].length));
return 'VOICE ready';
})()
