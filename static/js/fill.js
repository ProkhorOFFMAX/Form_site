document.addEventListener('DOMContentLoaded', function() {

    // --- 1. Загрузка вариантов для custom_select ---
    document.querySelectorAll('.custom-select').forEach(async function(select) {
        const fieldId = select.dataset.fieldId;
        if (!fieldId) return;

        try {
            const response = await fetch(`/api/custom_fields/${fieldId}/options`);
            const options = await response.json();

            select.innerHTML = '<option value="">— выберите —</option>';
            options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.id;
                option.textContent = opt.label;
                select.appendChild(option);
            });
        } catch (err) {
            console.error('Ошибка загрузки custom_select:', err);
            select.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    });

    // --- 2. Загрузка вариантов для reference_text (datalist) ---
    document.querySelectorAll('input[data-dict-id]').forEach(async function(input) {
        const dictId = input.dataset.dictId;
        const datalist = document.getElementById(input.getAttribute('list'));
        if (!datalist) return;

        try {
            const response = await fetch(`/api/reference_items?dict_id=${dictId}`);
            const items = await response.json();

            items.forEach(item => {
                const option = document.createElement('option');
                option.value = item.label;
                datalist.appendChild(option);
            });
        } catch (err) {
            console.error('Ошибка загрузки reference_text:', err);
        }
    });

    // --- 3. Каскад для institution (тип → наименование) ---
    document.querySelectorAll('.inst-type').forEach(function(typeSelect) {
        typeSelect.addEventListener('change', async function() {
            const type = this.value;
            const nameSelect = this.nextElementSibling;
            if (!nameSelect || !nameSelect.classList.contains('inst-name')) return;

            nameSelect.innerHTML = '<option value="">— загрузка... —</option>';

            try {
                const response = await fetch(`/api/institutions/${encodeURIComponent(type)}`);
                const data = await response.json();

                nameSelect.innerHTML = '<option value="">— выберите ОУ —</option>';
                data.forEach(item => {
                    const opt = document.createElement('option');
                    opt.value = item.id;
                    opt.textContent = item.short_name;
                    nameSelect.appendChild(opt);
                });
            } catch (err) {
                nameSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
            }
        });
    });

    // --- 4. Сохранение ответа ---
    const btnSave = document.getElementById('btn-save');
    if (!btnSave) return;

    btnSave.addEventListener('click', async function() {
        const templateId = parseInt(this.dataset.templateId);
        const answers = {};
        let hasError = false;

        document.querySelectorAll('#form-container [name]').forEach(function(input) {
            const name = input.name;

            // Пропускаем служебные поля
            if (name.endsWith('_type')) return;

            if (name.endsWith('_original')) {
                const fieldId = name.replace('_original', '');
                answers[fieldId] = {
                    original: input.value.trim(),
                    linked_id: null
                };
                return;
            }

            if (input.tagName === 'SELECT') {
                if (input.value === '') {
                    if (input.required) hasError = true;
                    return;
                }
                if (input.value === 'true' || input.value === 'false') {
                    answers[name] = input.value === 'true';
                } else {
                    answers[name] = input.value;
                }
            } else if (input.type === 'number') {
                answers[name] = input.value ? parseFloat(input.value) : null;
            } else {
                answers[name] = input.value.trim();
            }
        });

        if (hasError) {
            showError('Заполните все обязательные поля');
            return;
        }

        try {
            const response = await fetch('/api/responses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ template_id: templateId, answers })
            });
            const data = await response.json();

            if (data.success) {
                window.location.href = `/responses/${templateId}`;
            } else {
                showError(data.error || 'Ошибка сохранения');
            }
        } catch (err) {
            showError('Сетевая ошибка: ' + err.message);
        }
    });

    function showError(msg) {
        const el = document.getElementById('error-message');
        if (!el) return;
        el.textContent = msg;
        el.style.display = 'block';
    }
});