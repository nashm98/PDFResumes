const form = document.getElementById('upload-form');
const fileInput = document.getElementById('file');
const statusEl = document.getElementById('status');
const summarySection = document.getElementById('summary-section');
const summaryOutput = document.getElementById('summary-output');
const quizSection = document.getElementById('quiz-section');
const quizOutput = document.getElementById('quiz-output');
const submitBtn = document.getElementById('submit-btn');

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? '#ffb4b4' : '#a9b7da';
}

function showSection(section) {
  section.hidden = false;
  section.classList.remove('hidden');
}

function hideSection(section) {
  section.hidden = true;
  section.classList.add('hidden');
}

function renderQuiz(quiz) {
  quizOutput.innerHTML = '';

  if (!Array.isArray(quiz) || quiz.length === 0) {
    quizOutput.innerHTML = '<p>No fue posible generar preguntas para este documento.</p>';
    return;
  }

  quiz.forEach((item, index) => {
    const wrapper = document.createElement('article');
    wrapper.className = 'quiz-question';

    const title = document.createElement('h3');
    title.textContent = `${index + 1}. ${item.question}`;
    wrapper.appendChild(title);

    const list = document.createElement('ul');
    list.className = 'options';

    (item.options || []).forEach((option) => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'option-btn';
      btn.textContent = option;

      btn.addEventListener('click', () => {
        const allButtons = list.querySelectorAll('button');
        allButtons.forEach((b) => {
          b.disabled = true;
          if (b.textContent === item.answer) b.classList.add('correct');
        });

        if (option !== item.answer) btn.classList.add('wrong');
      });

      li.appendChild(btn);
      list.appendChild(li);
    });

    wrapper.appendChild(list);
    quizOutput.appendChild(wrapper);
  });
}

async function responseToJsonSafe(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(text || 'Respuesta inválida del servidor.');
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    setStatus('Debes seleccionar un archivo.', true);
    return;
  }

  hideSection(summarySection);
  hideSection(quizSection);
  summaryOutput.textContent = '';
  quizOutput.innerHTML = '';

  const body = new FormData();
  body.append('file', file);

  submitBtn.disabled = true;
  setStatus('Procesando documento...');

  try {
    const response = await fetch('./api/process', {
      method: 'POST',
      body,
    });

    const data = await responseToJsonSafe(response);
    if (!response.ok) {
      throw new Error(data.error || 'Error inesperado al procesar el archivo.');
    }

    summaryOutput.textContent = data.summary || 'No se pudo generar resumen.';
    renderQuiz(data.quiz || []);

    showSection(summarySection);
    showSection(quizSection);
    setStatus(`Archivo procesado: ${data.filename} (${data.text_length} caracteres leídos).`);
  } catch (error) {
    setStatus(error.message || 'Ocurrió un error al procesar el archivo.', true);
  } finally {
    submitBtn.disabled = false;
  }
});
