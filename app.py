from flask import Flask, request, jsonify, render_template_string
import urllib.request
import urllib.parse
import json
import os

app = Flask(__name__)
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>مترجم مقابلة العمل</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #0f0f0f; color: #e5e5e5; padding: 20px; min-height: 100vh; }
h1 { font-size: 20px; font-weight: 500; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.badge { font-size: 12px; padding: 3px 10px; border-radius: 20px; background: #1e1e1e; color: #888; }
.badge.active { background: #0d2e1a; color: #4ade80; }
.controls { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
button { padding: 10px 20px; border-radius: 8px; border: 1px solid #333; background: #1a1a1a; color: #e5e5e5; font-size: 15px; cursor: pointer; display: flex; align-items: center; gap: 8px; }
button:hover { background: #252525; }
#micBtn.recording { background: #2d0f0f; border-color: #7f1d1d; color: #f87171; }
.dot { width:10px;height:10px;border-radius:50%;background:#555;display:inline-block; }
.pulse { width:10px;height:10px;border-radius:50%;background:#ef4444;display:inline-block;animation:pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.3)} }
.status { font-size: 13px; color: #666; }
.card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; }
.label { font-size: 12px; color: #666; margin-bottom: 10px; }
.content { font-size: 17px; line-height: 1.6; min-height: 50px; color: #e5e5e5; direction: ltr; text-align: left; }
.translation { font-size: 19px; font-weight: 500; line-height: 1.6; min-height: 50px; color: #e5e5e5; direction: rtl; text-align: right; }
.placeholder { color: #444; font-style: italic; }
.accent-card { border-color: #1d3a5f; background: #0d1e33; }
.accent-label { color: #3b82f6; }
.suggest-label { font-size: 12px; color: #3b82f6; margin-bottom: 6px; margin-top: 12px; border-top: 1px solid #1d3a5f; padding-top: 12px; }
.suggest-text { font-size: 16px; color: #e5e5e5; direction: ltr; text-align: left; line-height: 1.6; }
.error { background: #2d0f0f; border: 1px solid #7f1d1d; border-radius: 8px; padding: 10px 14px; color: #f87171; font-size: 14px; margin-bottom: 14px; display: none; }
.history { margin-top: 20px; }
.history-title { font-size: 12px; color: #555; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; }
.history-item { background: #141414; border: 1px solid #222; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; }
.history-en { font-size: 13px; color: #666; margin-bottom: 4px; direction: ltr; text-align: left; }
.history-ar { font-size: 15px; color: #ccc; direction: rtl; text-align: right; }
</style>
</head>
<body>
<h1>🎯 مترجم مقابلة العمل <span class="badge" id="badge">غير نشط</span></h1>
<div class="controls">
  <button id="micBtn" onclick="toggleMic()"><span class="dot" id="indicator"></span><span id="micLabel">ابدأ الاستماع</span></button>
  <button onclick="clearAll()" style="padding:10px 14px;">🗑 مسح</button>
  <span class="status" id="statusText">اضغط لبدء الاستماع</span>
</div>
<div class="error" id="errorBox"></div>
<div class="card">
  <div class="label">ما يُقال بالإنجليزية</div>
  <div class="content" id="englishText"><span class="placeholder">سيظهر النص هنا عند الاستماع...</span></div>
</div>
<div class="card accent-card">
  <div class="label accent-label">الترجمة بالعربية</div>
  <div class="translation" id="arabicText"><span class="placeholder">ستظهر الترجمة هنا...</span></div>
  <div id="suggestArea"></div>
</div>
<div class="history" id="historySection" style="display:none">
  <div class="history-title">السجل</div>
  <div id="historyList"></div>
</div>
<script>
let recognition=null,isRecording=false,translating=false,lastTranslated='';
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
function showError(msg){const b=document.getElementById('errorBox');b.textContent=msg;b.style.display='block';setTimeout(()=>b.style.display='none',6000);}
function toggleMic(){if(!SR){showError('استخدم Chrome');return;}isRecording?stopMic():startMic();}
function startMic(){
  recognition=new SR();recognition.lang='en-US';recognition.continuous=true;recognition.interimResults=true;
  recognition.onstart=()=>{isRecording=true;document.getElementById('micBtn').classList.add('recording');document.getElementById('indicator').className='pulse';document.getElementById('micLabel').textContent='جارٍ الاستماع...';document.getElementById('badge').textContent='نشط';document.getElementById('badge').className='badge active';document.getElementById('statusText').textContent='يستمع الآن';};
  recognition.onresult=(e)=>{let final='',interim='';for(let i=e.resultIndex;i<e.results.length;i++){const t=e.results[i][0].transcript;e.results[i].isFinal?final+=t:interim+=t;}const txt=final||interim;if(txt){document.getElementById('englishText').textContent=txt;if(final&&final.trim().length>3&&final.trim()!==lastTranslated){lastTranslated=final.trim();translateText(final.trim());}}};
  recognition.onerror=(e)=>{if(e.error==='no-speech')return;showError('خطأ: '+e.error);stopMic();};
  recognition.onend=()=>{if(isRecording)recognition.start();};
  recognition.start();
}
function stopMic(){isRecording=false;if(recognition){recognition.onend=null;recognition.stop();}document.getElementById('micBtn').classList.remove('recording');document.getElementById('indicator').className='dot';document.getElementById('micLabel').textContent='ابدأ الاستماع';document.getElementById('badge').textContent='غير نشط';document.getElementById('badge').className='badge';document.getElementById('statusText').textContent='اضغط لبدء الاستماع';}
async function translateText(text){
  if(translating)return;translating=true;
  document.getElementById('arabicText').innerHTML='<span class="placeholder">جارٍ الترجمة...</span>';
  document.getElementById('suggestArea').innerHTML='';
  try{
    const resp=await fetch('/translate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});
    const data=await resp.json();
    document.getElementById('arabicText').textContent=data.translation;
    let extra='';
    if(data.suggestion) extra+=`<div class="suggest-label">رد مقترح بالإنجليزية</div><div class="suggest-text">${data.suggestion}</div>`;
    document.getElementById('suggestArea').innerHTML=extra;
    addHistory(text,data.translation);
  }catch(err){document.getElementById('arabicText').innerHTML='<span style="color:#f87171">تعذّرت الترجمة</span>';}
  translating=false;
}
function addHistory(en,ar){document.getElementById('historySection').style.display='block';const item=document.createElement('div');item.className='history-item';item.innerHTML=`<div class="history-en">${en}</div><div class="history-ar">${ar}</div>`;document.getElementById('historyList').prepend(item);if(document.getElementById('historyList').children.length>10)document.getElementById('historyList').lastChild.remove();}
function clearAll(){document.getElementById('englishText').innerHTML='<span class="placeholder">سيظهر النص هنا عند الاستماع...</span>';document.getElementById('arabicText').innerHTML='<span class="placeholder">ستظهر الترجمة هنا...</span>';document.getElementById('suggestArea').innerHTML='';document.getElementById('historySection').style.display='none';document.getElementById('historyList').innerHTML='';lastTranslated='';}
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/translate', methods=['POST'])
def translate():
    text = request.json.get('text', '')

    translation = ''
    suggestion = ''

    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 400,
            "messages": [{
                "role": "user",
                "content": f"""You are helping someone in a job interview. The interviewer said: "{text}"

Do two things:
1. Translate the sentence naturally to Arabic (not word by word, make it sound natural)
2. Write a short simple answer in English the person can say (max 2 sentences, easy words)

Reply in this exact format:
TRANSLATION: [Arabic translation here]
REPLY: [English answer here]"""
            }]
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': API_KEY,
                'anthropic-version': '2023-06-01'
            }
        )
        resp = urllib.request.urlopen(req, timeout=15)
        rdata = json.loads(resp.read())
        raw = rdata['content'][0]['text'].strip()

        import re
        t = re.search(r'TRANSLATION:\s*(.+?)(?:\nREPLY:|$)', raw, re.DOTALL)
        r = re.search(r'REPLY:\s*(.+)', raw, re.DOTALL)
        translation = t.group(1).strip() if t else raw
        suggestion = r.group(1).strip() if r else ''

    except Exception as e:
        translation = text
        suggestion = ''

    return jsonify({'translation': translation, 'suggestion': suggestion})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
