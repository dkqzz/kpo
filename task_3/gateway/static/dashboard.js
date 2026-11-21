const uploadForm = document.querySelector('#upload-form');
const reportsForm = document.querySelector('#reports-form');
const reportAssignment = document.querySelector('#report-assignment');
const uploadStatus = document.querySelector('#upload-status');
const reportsStatus = document.querySelector('#reports-status');
const summary = document.querySelector('#summary');
const reportList = document.querySelector('#report-list');
const reportTemplate = document.querySelector('#report-template');
const labels = { passed: 'Проверка пройдена', failed: 'Проверка не пройдена', no_report: 'Нет отчёта' };
const dateFormat = new Intl.DateTimeFormat('ru', { dateStyle: 'short', timeStyle: 'short' });
let requestedReports = 0;

async function requestJson(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.error?.message || 'Не удалось выполнить запрос.');
    error.submissionId = payload.error?.submission_id;
    throw error;
  }
  return payload;
}

function showMessage(element, message, state = '') {
  element.textContent = message;
  element.dataset.state = state;
  element.hidden = !message;
}

async function loadReports(assignmentId) {
  const requestId = ++requestedReports;
  const button = reportsForm.querySelector('button[type="submit"]');
  button.disabled = true;
  reportList.setAttribute('aria-busy', 'true');
  reportList.replaceChildren();
  summary.hidden = true;
  showMessage(reportsStatus, 'Загружаем отчёты…');
  try {
    const path = `/assignments/${encodeURIComponent(assignmentId)}/reports`;
    const data = await requestJson(path);
    if (requestId !== requestedReports) return;
    for (const [key, count] of Object.entries(data.summary)) {
      document.getElementById(key).textContent = count;
    }
    summary.hidden = false;
    for (const row of data.submissions) {
      reportList.append(renderReport(row, assignmentId));
    }
    showMessage(reportsStatus, data.summary.total ? '' : 'По этому заданию пока нет сдач.');
  } catch (error) {
    if (requestId === requestedReports) showMessage(reportsStatus, error.message, 'failed');
  } finally {
    if (requestId === requestedReports) {
      button.disabled = false;
      reportList.setAttribute('aria-busy', 'false');
    }
  }
}

function renderReport(row, assignmentId) {
  const item = reportTemplate.content.firstElementChild.cloneNode(true);
  const status = item.querySelector('[data-field="status"]');
  const details = item.querySelector('[data-field="details"]');
  const { submission } = row;
  item.querySelector('[data-field="student"]').textContent = submission.student_id;
  status.textContent = labels[row.status];
  status.dataset.state = row.status;
  const date = dateFormat.format(new Date(submission.submitted_at));
  item.querySelector('[data-field="artifact"]').textContent = `${submission.filename} · ${date}`;
  details.textContent = row.report?.details || 'Файл сохранён. Анализ можно запустить повторно.';

  if (!row.report) {
    const button = item.querySelector('.retry');
    button.hidden = false;
    button.addEventListener('click', async () => {
      button.disabled = true;
      details.textContent = 'Проверяем…';
      try {
        await requestJson(`/submissions/${submission.submission_id}/analysis`, { method: 'POST' });
        if (item.isConnected) await loadReports(assignmentId);
      } catch (error) {
        details.textContent = error.message;
      } finally {
        button.disabled = false;
      }
    });
  }
  return item;
}

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = uploadForm.querySelector('button[type="submit"]');
  const formData = new FormData(uploadForm);
  const assignmentId = formData.get('assignment_id').trim();
  button.disabled = true;
  showMessage(uploadStatus, 'Сохраняем файл и проверяем…');
  try {
    const { report } = await requestJson(uploadForm.action, { method: 'POST', body: formData });
    showMessage(uploadStatus, `${labels[report.status]}. ${report.details}`, report.status);
    reportAssignment.value = assignmentId;
    await loadReports(assignmentId);
  } catch (error) {
    const message = error.submissionId ? `${error.message} ID сдачи ${error.submissionId}` : error.message;
    showMessage(uploadStatus, message, 'failed');
  } finally {
    button.disabled = false;
  }
});

reportsForm.addEventListener('submit', (event) => {
  event.preventDefault();
  loadReports(reportAssignment.value.trim());
});
