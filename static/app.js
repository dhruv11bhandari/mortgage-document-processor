const $ = (s) => document.querySelector(s);
const uploadDialog = $('#upload-dialog');
const detailDialog = $('#detail-dialog');
const fileInput = $('#file-input');
let selectedFile = null;
let jobsCache = [];
$('#today').textContent = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric' }).format(new Date());

function safe(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function dateLabel(value) { if (!value) return 'Just now'; const d = new Date(value); return Number.isNaN(d.getTime()) ? 'Just now' : new Intl.DateTimeFormat(undefined, {month:'short',day:'numeric'}).format(d); }
function filenameLabel(job) { return job.file_name || 'Mortgage package'; }
async function refreshJobs() {
  const body = $('#job-list');
  try {
    const response = await fetch('/api/jobs');
    if (!response.ok) throw new Error('Could not load packages');
    jobsCache = await response.json();
    const completed = jobsCache.filter(j => j.status === 'completed');
    $('#metric-packages').textContent = completed.length;
    $('#metric-pages').textContent = completed.reduce((n,j) => n + (j.page_count || 0),0).toLocaleString();
    $('#metric-attention').textContent = completed.reduce((n,j) => n + (j.exceptions || []).length,0).toLocaleString();
    $('#nav-count').textContent = jobsCache.length;
    $('#empty-state').hidden = jobsCache.length > 0;
    if (!jobsCache.length) { body.innerHTML = ''; return; }
    body.innerHTML = jobsCache.map((job,i) => {
      const status = job.status === 'failed' ? 'Failed' : job.status === 'queued' || job.status === 'processing' ? 'Processing' : (job.exceptions || []).length ? 'Review flags' : 'Ready';
      const cls = status === 'Failed' ? 'failed' : status === 'Review flags' ? 'attention' : '';
      return `<tr><td><span class="file-badge">PDF</span>${safe(filenameLabel(job))}</td><td>${job.page_count ?? '—'}</td><td>${job.documents?.length ?? '—'}</td><td><span class="status-pill ${cls}">${status === 'Processing' ? '<span class="spinner"></span>' : ''}${status}</span></td><td><button class="row-action" data-job="${safe(job.job_id)}" aria-label="View package">›</button></td></tr>`;
    }).join('');
    body.querySelectorAll('[data-job]').forEach(button => button.addEventListener('click', () => showDetail(button.dataset.job)));
    if (jobsCache.some(j => j.status === 'queued' || j.status === 'processing')) setTimeout(refreshJobs, 1800);
  } catch (err) { body.innerHTML = `<tr><td colspan="5" class="loading-row">${safe(err.message)}</td></tr>`; }
}
function openUpload() { selectedFile = null; fileInput.value = ''; $('#selected-file').hidden = true; $('#upload-error').hidden = true; $('#submit-upload').disabled = true; uploadDialog.showModal(); }
$('#new-package').addEventListener('click', openUpload);
$('#empty-upload').addEventListener('click', openUpload);
$('#cancel-upload').addEventListener('click', () => uploadDialog.close());
$('#refresh').addEventListener('click', refreshJobs);
$('#dropzone').addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => selectFile(fileInput.files[0]));
function selectFile(file) {
  if (!file) return;
  const error = $('#upload-error');
  if (!file.name.toLowerCase().endsWith('.pdf')) { error.textContent = 'Choose a PDF file.'; error.hidden = false; return; }
  if (file.size > 50 * 1024 * 1024) { error.textContent = 'This file is larger than 50 MB.'; error.hidden = false; return; }
  selectedFile = file; error.hidden = true;
  $('#selected-file').textContent = `▧  ${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MB`;
  $('#selected-file').hidden = false; $('#submit-upload').disabled = false;
}
const dropzone = $('#dropzone');
['dragenter','dragover'].forEach(type => dropzone.addEventListener(type, e => { e.preventDefault(); dropzone.classList.add('drag'); }));
['dragleave','drop'].forEach(type => dropzone.addEventListener(type, e => { e.preventDefault(); dropzone.classList.remove('drag'); }));
dropzone.addEventListener('drop', e => selectFile(e.dataTransfer.files[0]));
$('#submit-upload').addEventListener('click', async () => {
  if (!selectedFile) return;
  const button = $('#submit-upload'); button.disabled = true; button.textContent = 'Uploading…';
  try {
    const data = new FormData(); data.append('file', selectedFile);
    const response = await fetch('/api/jobs', {method:'POST',body:data});
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Upload failed');
    uploadDialog.close(); await refreshJobs();
  } catch (err) {
    $('#upload-error').textContent = err.message; $('#upload-error').hidden = false;
  } finally { button.disabled = !selectedFile; button.innerHTML = 'Process package <span>→</span>'; }
});
async function showDetail(id) {
  const job = jobsCache.find(j => j.job_id === id);
  if (!job) return;
  const content = $('#detail-content');
  if (job.status === 'queued' || job.status === 'processing') {
    content.innerHTML = `<div class="modal-mark">◌</div><div class="section-kicker">PACKAGE PROCESSING</div><h2 class="detail-title">${safe(filenameLabel(job))}</h2><p class="detail-meta">Your package is being processed locally. This view will refresh shortly.</p>`;
    detailDialog.showModal(); setTimeout(async () => { await refreshJobs(); if (detailDialog.open) showDetail(id); }, 1800); return;
  }
  if (job.status === 'failed') {
    content.innerHTML = `<div class="modal-mark">!</div><div class="section-kicker">PROCESSING ERROR</div><h2 class="detail-title">${safe(filenameLabel(job))}</h2><p class="detail-meta">${safe(job.error || 'The package could not be processed.')}</p>`;
    detailDialog.showModal(); return;
  }
  const documents = (job.documents || []).map(doc => `<div class="detail-doc"><span><strong>${safe(doc.type.replaceAll('_',' '))}</strong> · ${doc.pages} page${doc.pages === 1 ? '' : 's'} · pages ${(doc.source_pages || []).join(', ')}</span><a href="/api/jobs/${encodeURIComponent(id)}/documents/${encodeURIComponent(doc.path)}" download>Download ↓</a></div>`).join('') || '<p class="detail-meta">No documents were confidently identified.</p>';
  const flags = (job.exceptions || []).map(ex => `<div class="exception">${safe(ex.type.replaceAll('_',' '))}${ex.page ? ` · page ${ex.page}` : ''} · ${safe(ex.severity)}</div>`).join('');
  content.innerHTML = `<div class="modal-mark">▤</div><div class="section-kicker">PACKAGE REVIEW</div><h2 class="detail-title">${safe(filenameLabel(job))}</h2><p class="detail-meta">${job.page_count} pages · ${job.documents?.length || 0} document groups · added ${dateLabel(job.created_at)}</p><div class="detail-list">${documents}</div>${flags ? `<div class="section-kicker">REVIEW FLAGS</div>${flags}` : '<p class="detail-meta">No automated review flags. Always verify extracted classifications.</p>'}<div class="modal-actions"><a class="button secondary" href="/api/jobs/${encodeURIComponent(id)}" target="_blank">View manifest ↗</a></div>`;
  detailDialog.showModal();
}
refreshJobs();
