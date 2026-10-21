const $ = (selector) => document.querySelector(selector);
const uploadDialog = $('#upload-dialog');
const detailDialog = $('#detail-dialog');
const fileInput = $('#file-input');
let selectedFile = null;
let jobsCache = [];
let demoMode = false;
const query = new URLSearchParams(window.location.search);
const apiBase = (window.MORTGAGE_API_BASE || query.get('api') || $('meta[name="mortgage-api-base"]')?.content || '').replace(/\/+$/, '');
const forceDemoMode = query.get('demo') === '1';
const apiUrl = (path) => `${apiBase}${path}`;

const demoJobs = [{
  job_id: 'demo-sample-package',
  status: 'completed',
  is_demo: true,
  file_name: 'Sample mortgage package.pdf',
  created_at: '2026-01-15T10:30:00Z',
  page_count: 24,
  documents: [
    { type: '1003_form', pages: 8, source_pages: [1, 2, 3, 4, 5, 6, 7, 8], average_confidence: 0.83 },
    { type: 'bank_stmt', pages: 6, source_pages: [9, 10, 11, 12, 13, 14], average_confidence: 0.72 },
    { type: 'pay_stub', pages: 2, source_pages: [15, 16], average_confidence: 0.60 },
    { type: 'unknown', pages: 8, source_pages: [17, 18, 19, 20, 21, 22, 23, 24], average_confidence: 0 }
  ],
  exceptions: [
    { type: 'UNCLASSIFIED_PAGE', page: 18, severity: 'WARNING' },
    { type: 'OCR_UNAVAILABLE', page: 22, severity: 'WARNING' }
  ]
}];

$('#today').textContent = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric' }).format(new Date());

function safe(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}
function dateLabel(value) {
  if (!value) return 'Just now';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Just now' : new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date);
}
function filenameLabel(job) { return job.file_name || 'Mortgage package'; }

function setDemoBanner(message) {
  let banner = $('#demo-banner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'demo-banner';
    banner.className = 'demo-banner';
    $('.package-panel .panel-heading').insertAdjacentElement('afterend', banner);
  }
  banner.textContent = message;
  banner.hidden = false;
}
function clearDemoBanner() {
  const banner = $('#demo-banner');
  if (banner) banner.hidden = true;
}
function useDemoFallback(message) {
  demoMode = true;
  jobsCache = demoJobs;
  setDemoBanner(message || 'Demo mode · The backend is unavailable. Sample data only; no documents were processed.');
  renderJobs();
}
function renderJobs() {
  const body = $('#job-list');
  const completed = jobsCache.filter((job) => job.status === 'completed');
  $('#metric-packages').textContent = completed.length;
  $('#metric-pages').textContent = completed.reduce((count, job) => count + (job.page_count || 0), 0).toLocaleString();
  $('#metric-attention').textContent = completed.reduce((count, job) => count + (job.exceptions || []).length, 0).toLocaleString();
  $('#nav-count').textContent = jobsCache.length;
  $('#empty-state').hidden = jobsCache.length > 0;
  if (!jobsCache.length) { body.innerHTML = ''; return; }

  body.innerHTML = jobsCache.map((job) => {
    const status = job.is_demo ? 'Demo preview' : job.status === 'failed' ? 'Failed' :
      job.status === 'queued' || job.status === 'processing' ? 'Processing' :
        (job.exceptions || []).length ? 'Review flags' : 'Ready';
    const statusClass = job.is_demo ? 'demo' : status === 'Failed' ? 'failed' : status === 'Review flags' ? 'attention' : '';
    return `<tr><td><span class="file-badge">PDF</span>${safe(filenameLabel(job))}${job.is_demo ? ' <span class="demo-tag">SAMPLE</span>' : ''}</td><td>${job.page_count ?? '—'}</td><td>${job.documents?.length ?? '—'}</td><td><span class="status-pill ${statusClass}">${status === 'Processing' ? '<span class="spinner"></span>' : ''}${status}</span></td><td><button class="row-action" data-job="${safe(job.job_id)}" aria-label="View package">›</button></td></tr>`;
  }).join('');
  body.querySelectorAll('[data-job]').forEach((button) => button.addEventListener('click', () => showDetail(button.dataset.job)));
}

async function refreshJobs() {
  if (forceDemoMode) {
    useDemoFallback('Demo preview · Sample data only; no documents were uploaded or processed.');
    return;
  }
  try {
    const response = await fetch(apiUrl('/api/jobs'));
    if (!response.ok) throw new Error(`Workspace API returned ${response.status}`);
    const jobs = await response.json();
    if (!Array.isArray(jobs)) throw new Error('Workspace API returned an unexpected response');
    demoMode = false;
    jobsCache = jobs;
    clearDemoBanner();
    renderJobs();
    if (jobsCache.some((job) => job.status === 'queued' || job.status === 'processing')) setTimeout(refreshJobs, 1800);
  } catch (error) {
    useDemoFallback('Demo mode · Backend unavailable. Sample data only; uploads will not be processed.');
  }
}

function openUpload() {
  selectedFile = null;
  fileInput.value = '';
  $('#selected-file').hidden = true;
  $('#upload-error').hidden = true;
  $('#submit-upload').disabled = true;
  if (!uploadDialog.open) uploadDialog.showModal();
}
[$('#new-package'), $('#empty-upload')].forEach((button) => {
  button?.addEventListener('click', (event) => {
    event.preventDefault();
    openUpload();
  });
});
$('#demo-preview')?.addEventListener('click', () => useDemoFallback('Demo preview · Sample data only; no documents were uploaded or processed.'));
$('#cancel-upload').addEventListener('click', () => uploadDialog.close());
$('#refresh').addEventListener('click', refreshJobs);
// The dropzone is a label for the file input. Let the browser's native label
// activation open the picker; manually calling input.click() here can be
// blocked by some browsers when the input itself is hidden.
fileInput.addEventListener('change', () => selectFile(fileInput.files[0]));
function selectFile(file) {
  if (!file) return;
  const error = $('#upload-error');
  if (!file.name.toLowerCase().endsWith('.pdf')) { error.textContent = 'Choose a PDF file.'; error.hidden = false; return; }
  if (file.size > 50 * 1024 * 1024) { error.textContent = 'This file is larger than 50 MB.'; error.hidden = false; return; }
  selectedFile = file;
  error.hidden = true;
  $('#selected-file').textContent = `▧  ${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MB`;
  $('#selected-file').hidden = false;
  $('#submit-upload').disabled = false;
}
const dropzone = $('#dropzone');
['dragenter', 'dragover'].forEach((type) => dropzone.addEventListener(type, (event) => { event.preventDefault(); dropzone.classList.add('drag'); }));
['dragleave', 'drop'].forEach((type) => dropzone.addEventListener(type, (event) => { event.preventDefault(); dropzone.classList.remove('drag'); }));
dropzone.addEventListener('drop', (event) => selectFile(event.dataTransfer.files[0]));

$('#submit-upload').addEventListener('click', async () => {
  if (!selectedFile) return;
  const button = $('#submit-upload');
  button.disabled = true;
  button.innerHTML = 'Uploading…';
  try {
    if (forceDemoMode) throw new Error('Demo preview is view-only. The selected file was not processed.');
    const data = new FormData();
    data.append('file', selectedFile);
    const response = await fetch(apiUrl('/api/jobs'), { method: 'POST', body: data });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || 'Upload failed');
    uploadDialog.close();
    await refreshJobs();
  } catch (error) {
    useDemoFallback(forceDemoMode
      ? 'Demo preview · Sample data only; no documents were uploaded or processed.'
      : 'Demo mode · Backend unavailable. Sample data only; your selected file was not processed.');
    $('#upload-error').textContent = `${error.message || 'Backend unavailable.'} The sample workspace is shown instead; your file was not processed.`;
    $('#upload-error').hidden = false;
  } finally {
    button.disabled = !selectedFile;
    button.innerHTML = 'Process package <span>→</span>';
  }
});

async function showDetail(id) {
  const job = jobsCache.find((candidate) => candidate.job_id === id);
  if (!job) return;
  const content = $('#detail-content');
  if (job.status === 'queued' || job.status === 'processing') {
    content.innerHTML = `<div class="modal-mark">◌</div><div class="section-kicker">PACKAGE PROCESSING</div><h2 class="detail-title">${safe(filenameLabel(job))}</h2><p class="detail-meta">Your package is being processed locally. This view will refresh shortly.</p>`;
    detailDialog.showModal();
    setTimeout(async () => { await refreshJobs(); if (detailDialog.open) showDetail(id); }, 1800);
    return;
  }
  if (job.status === 'failed') {
    content.innerHTML = `<div class="modal-mark">!</div><div class="section-kicker">PROCESSING ERROR</div><h2 class="detail-title">${safe(filenameLabel(job))}</h2><p class="detail-meta">${safe(job.error || 'The package could not be processed.')}</p>`;
    detailDialog.showModal();
    return;
  }
  const documents = (job.documents || []).map((document) => {
    const label = `<strong>${safe(document.type.replaceAll('_', ' '))}</strong> · ${document.pages} page${document.pages === 1 ? '' : 's'} · pages ${(document.source_pages || []).join(', ')}`;
    const action = job.is_demo ? '<span class="demo-only">Sample only</span>' : `<a href="${apiUrl(`/api/jobs/${encodeURIComponent(id)}/documents/${encodeURIComponent(document.path)}`)}" download>Download ↓</a>`;
    return `<div class="detail-doc"><span>${label}</span>${action}</div>`;
  }).join('') || '<p class="detail-meta">No documents were confidently identified.</p>';
  const flags = (job.exceptions || []).map((exception) => `<div class="exception">${safe(exception.type.replaceAll('_', ' '))}${exception.page ? ` · page ${exception.page}` : ''} · ${safe(exception.severity)}</div>`).join('');
  const demoNote = job.is_demo ? '<div class="demo-disclaimer">Illustrative sample data only. No real document was uploaded or processed.</div>' : '';
  const manifestAction = job.is_demo ? '' : `<div class="modal-actions"><a class="button secondary" href="${apiUrl(`/api/jobs/${encodeURIComponent(id)}`)}" target="_blank">View manifest ↗</a></div>`;
  content.innerHTML = `<div class="modal-mark">▤</div><div class="section-kicker">${job.is_demo ? 'DEMO PREVIEW' : 'PACKAGE REVIEW'}</div><h2 class="detail-title">${safe(filenameLabel(job))}</h2><p class="detail-meta">${job.page_count} pages · ${job.documents?.length || 0} document groups · ${job.is_demo ? 'sample data' : `added ${dateLabel(job.created_at)}`}</p>${demoNote}<div class="detail-list">${documents}</div>${flags ? `<div class="section-kicker">REVIEW FLAGS</div>${flags}` : '<p class="detail-meta">No automated review flags. Always verify extracted classifications.</p>'}${manifestAction}`;
  detailDialog.showModal();
}

refreshJobs();
