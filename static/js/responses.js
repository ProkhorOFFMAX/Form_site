document.addEventListener('DOMContentLoaded', function() {
    const dialog = document.getElementById('edit-field-dialog');
    const title = document.getElementById('edit-field-title');
    const responseIdInput = document.getElementById('edit-response-id');
    const fieldIdInput = document.getElementById('edit-field-id');
    const inputContainer = document.getElementById('edit-field-input-container');
    const reasonInput = document.getElementById('edit-reason');

    // --- Открытие диалога ---
    document.querySelectorAll('.edit-field-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const responseId = this.dataset.responseId;
            const field = JSON.parse(this.dataset.field);
            const currentValue = JSON.parse(this.dataset.value || 'null');

            responseIdInput.value = responseId;
            fieldIdInput.value = field.id;
            title.textContent = `Редактировать: ${field.label}`;
            reasonInput.value = '';
            inputContainer.innerHTML = '';

            // --- Создаём input в зависимости от типа ---
            if (field.type === 'boolean') {
                const select = document.createElement('select');
                select.id = 'edit-field-input';
                select.innerHTML = `
                    <option value="true">Да</option>
                    <option value="false">Нет</option>
                `;
                select.value = currentValue === true ? 'true' : 'false';
                inputContainer.appendChild(select);

            } else if (field.type === 'number') {
                const input = document.createElement('input');
                input.id = 'edit-field-input';
                input.type = 'number';
                input.step = 'any';
                input.value = currentValue ?? '';
                inputContainer.appendChild(input);

            } else if (field.type === 'custom_select') {
                const select = document.createElement('select');
                select.id = 'edit-field-input';
                select.innerHTML = '<option value="">— загрузка... —</option>';
                inputContainer.appendChild(select);

                // Загружаем варианты
                fetch(`/api/custom_fields/${field.field_id}/options`)
                    .then(r => r.json())
                    .then(options => {
                        select.innerHTML = '<option value="">— выберите —</option>';
                        options.forEach(opt => {
                            const option = document.createElement('option');
                            option.value = opt.id;
                            option.textContent = opt.label;
                            if (opt.id === currentValue) option.selected = true;
                            select.appendChild(option);
                        });
                    })
                    .catch(() => {
                        select.innerHTML = '<option value="">Ошибка загрузки</option>';
                    });

            } else if (field.type === 'institution') {
                // Два select: тип + наименование
                const typeSelect = document.createElement('select');
                typeSelect.id = 'edit-inst-type';
                typeSelect.innerHTML = `
                    <option value="">— выберите тип —</option>
                    <option value="ГБОУ">ГБОУ</option>
                    <option value="ГБДОУ">ГБДОУ</option>
                    <option value="ОДОД">ОДОД</option>
                `;
                typeSelect.style.marginBottom = '8px';
                inputContainer.appendChild(typeSelect);

                const nameSelect = document.createElement('select');
                nameSelect.id = 'edit-field-input';
                nameSelect.innerHTML = '<option value="">— сначала выберите тип —</option>';
                inputContainer.appendChild(nameSelect);

                // Если уже есть значение — загружаем его и определяем тип
                if (currentValue) {
                    fetch(`/api/institutions/id/${currentValue}`)
                        .then(r => r.json())
                        .then(inst => {
                            if (inst && inst.type) {
                                typeSelect.value = inst.type;
                                // Загружаем список этого типа
                                return fetch(`/api/institutions/${encodeURIComponent(inst.type)}`);
                            }
                        })
                        .then(r => r && r.json())
                        .then(data => {
                            if (!data) return;
                            nameSelect.innerHTML = '<option value="">— выберите ОУ —</option>';
                            data.forEach(item => {
                                const opt = document.createElement('option');
                                opt.value = item.id;
                                opt.textContent = item.short_name;
                                if (item.id === currentValue) opt.selected = true;
                                nameSelect.appendChild(opt);
                            });
                        })
                        .catch(err => console.error('Ошибка загрузки ОУ:', err));
                }

                // При смене типа — загружаем наименования
                typeSelect.addEventListener('change', async function() {
                    const type = this.value;
                    nameSelect.innerHTML = '<option value="">— загрузка... —</option>';

                    if (!type) {
                        nameSelect.innerHTML = '<option value="">— сначала выберите тип —</option>';
                        return;
                    }

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

            } else if (field.type === 'reference_text') {
                const input = document.createElement('input');
                input.id = 'edit-field-input';
                input.type = 'text';
                input.value = (currentValue && currentValue.original) || '';
                input.setAttribute('list', 'edit-datalist');
                inputContainer.appendChild(input);

                const datalist = document.createElement('datalist');
                datalist.id = 'edit-datalist';
                inputContainer.appendChild(datalist);

                fetch(`/api/reference_items?dict_id=${field.dict_id}`)
                    .then(r => r.json())
                    .then(items => {
                        items.forEach(item => {
                            const opt = document.createElement('option');
                            opt.value = item.label;
                            datalist.appendChild(opt);
                        });
                    });

            } else {
                // text и всё остальное
                const input = document.createElement('input');
                input.id = 'edit-field-input';
                input.type = 'text';
                input.value = currentValue ?? '';
                inputContainer.appendChild(input);
            }

            dialog.showModal();
        });
    });

    // --- Сохранение ---
    document.getElementById('btn-save-field').addEventListener('click', async function() {
        const responseId = responseIdInput.value;
        const fieldId = fieldIdInput.value;
        const reason = reasonInput.value.trim();

        // Определяем, какой input сейчас в контейнере
        const input = document.getElementById('edit-field-input');
        if (!input) return;

        let newValue;

        if (input.tagName === 'SELECT') {
            if (input.value === '') {
                alert('Выберите значение');
                return;
            }
            if (input.value === 'true' || input.value === 'false') {
                newValue = input.value === 'true';
            } else {
                newValue = parseInt(input.value);  // для institution/custom_select
            }
        } else if (input.type === 'number') {
            newValue = input.value === '' ? null : parseFloat(input.value);
        } else if (input.hasAttribute('list')) {
            // reference_text — отправляем объект
            newValue = { original: input.value.trim(), linked_id: null };
        } else {
            newValue = input.value.trim();
        }

        try {
            const response = await fetch(`/api/responses/${responseId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ field_id: fieldId, new_value: newValue, reason })
            });
            const data = await response.json();

            if (data.success) {
                dialog.close();
                location.reload();
            } else {
                alert(data.error || 'Ошибка сохранения');
            }
        } catch (err) {
            alert('Сетевая ошибка: ' + err.message);
        }
    });
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('cancel')) {
            const dialog = e.target.closest('dialog');
            if (dialog) {
                dialog.close();
            }
        }
    });
});