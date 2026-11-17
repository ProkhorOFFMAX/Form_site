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

    document.querySelectorAll('.history-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const responseId = this.dataset.responseId;
            const response = await fetch(`/api/responses/${responseId}/history`);
            const history = await response.json();

            // Строим HTML для модального окна
            let html = '<h3>История изменений</h3><table border="1" cellpadding="5">';
            html += '<thead><tr><th>Когда</th><th>Кто</th><th>Поле</th><th>Было</th><th>Стало</th><th>Причина</th></tr></thead><tbody>';
            history.forEach(h => {
                html += `<tr>
                    <td>${h.changed_at}</td>
                    <td>${h.changed_by_email}</td>
                    <td>${h.field_id}</td>
                    <td>${JSON.stringify(h.old_value)}</td>
                    <td>${JSON.stringify(h.new_value)}</td>
                    <td>${h.change_reason || '—'}</td>
                </tr>`;
            });
            html += '</tbody></table>';

            // Показываем в диалоге
            // (нужен отдельный <dialog id="history-dialog"> в HTML)
        });
    });

    document.querySelectorAll('.edit-composite-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const responseId = this.dataset.responseId;
            const field = JSON.parse(this.dataset.field);
            const currentValue = JSON.parse(this.dataset.value || '{}');

            document.getElementById('edit-composite-response-id').value = responseId;
            document.getElementById('edit-composite-field-id').value = field.id;
            document.getElementById('edit-composite-title').textContent = `Редактировать: ${field.label}`;
            document.getElementById('edit-composite-reason').value = '';

            const partsContainer = document.getElementById('edit-composite-parts');
            partsContainer.innerHTML = '';

            // Рендерим каждую часть
            field.parts.forEach(part => {
                const wrapper = document.createElement('div');
                wrapper.style.marginBottom = '10px';

                const label = document.createElement('label');
                label.textContent = part.label + ': ';
                label.style.display = 'block';
                label.style.marginBottom = '4px';
                wrapper.appendChild(label);

                const val = currentValue[part.name];

                if (part.type === 'boolean') {
                    const select = document.createElement('select');
                    select.innerHTML = '<option value="true">Да</option><option value="false">Нет</option>';
                    select.value = val === true ? 'true' : 'false';
                    select.dataset.partName = part.name;
                    select.dataset.partType = 'boolean';
                    select.style.width = '100%';
                    select.style.padding = '6px';
                    wrapper.appendChild(select);

                } else if (part.type === 'number') {
                    const input = document.createElement('input');
                    input.type = 'number';
                    input.step = 'any';
                    input.value = val ?? '';
                    input.dataset.partName = part.name;
                    input.dataset.partType = 'number';
                    input.style.width = '100%';
                    input.style.padding = '6px';
                    wrapper.appendChild(input);

                } else if (part.type === 'custom_select') {
                    const select = document.createElement('select');
                    select.dataset.partName = part.name;
                    select.dataset.partType = 'custom_select';
                    select.style.width = '100%';
                    select.style.padding = '6px';
                    select.innerHTML = '<option value="">— загрузка... —</option>';
                    // Загружаем варианты
                    fetch(`/api/custom_fields/${part.field_id}/options`)
                        .then(r => r.json())
                        .then(options => {
                            select.innerHTML = '<option value="">— выберите —</option>';
                            options.forEach(opt => {
                                const o = document.createElement('option');
                                o.value = opt.id;
                                o.textContent = opt.label;
                                if (parseInt(opt.id) === parseInt(val)) o.selected = true;
                                select.appendChild(o);
                            });
                        });
                    wrapper.appendChild(select);

                } else if (part.type === 'institution') {
                    // Упрощённо: input с ID (или можно сделать каскад, как в fill.js)
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.value = val ?? '';
                    input.placeholder = 'ID ОУ';
                    input.dataset.partName = part.name;
                    input.dataset.partType = 'institution';
                    input.style.width = '100%';
                    input.style.padding = '6px';
                    wrapper.appendChild(input);

                } else if (part.type === 'reference_text') {
                    // input + datalist
                    const listId = 'composite-datalist-' + Math.random().toString(36).substr(2, 9);

                    const input = document.createElement('input');
                    input.type = 'text';
                    input.value = (val && val.original) ? val.original : (val ?? '');
                    input.dataset.partName = part.name;
                    input.dataset.partType = 'reference_text';
                    input.dataset.linkedId = (val && val.linked_id) ? val.linked_id : '';
                    input.setAttribute('list', listId);
                    input.style.width = '100%';
                    input.style.padding = '6px';

                    const datalist = document.createElement('datalist');
                    datalist.id = listId;

                    // Загружаем значения словаря
                    fetch(`/api/reference_items?dict_id=${part.dict_id}`)
                        .then(r => r.json())
                        .then(items => {
                            items.forEach(item => {
                                const o = document.createElement('option');
                                o.value = item.label;
                                datalist.appendChild(o);
                            });
                        });

                    wrapper.appendChild(input);
                    wrapper.appendChild(datalist);

                } else {
                    // text и остальные
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.value = val ?? '';
                    input.dataset.partName = part.name;
                    input.dataset.partType = part.type || 'text';
                    input.style.width = '100%';
                    input.style.padding = '6px';
                    wrapper.appendChild(input);
                }

                partsContainer.appendChild(wrapper);
            });

            document.getElementById('edit-composite-dialog').showModal();
        });
    });

    document.getElementById('btn-save-composite').addEventListener('click', async function() {
        const responseId = document.getElementById('edit-composite-response-id').value;
        const fieldId = document.getElementById('edit-composite-field-id').value;
        const reason = document.getElementById('edit-composite-reason').value.trim();

        const newValue = {};
        document.querySelectorAll('#edit-composite-parts [data-part-name]').forEach(input => {
            const partName = input.dataset.partName;
            const partType = input.dataset.partType;
            let val = input.value.trim();

            if (val === '') return;

            if (partType === 'number') {
                val = parseFloat(val);
            } else if (partType === 'boolean') {
                val = (val === 'true');
            } else if (partType === 'custom_select' || partType === 'institution') {
                val = parseInt(val);
            } else if (partType === 'reference_text') {
                // Сохраняем объект с original и (опционально) linked_id
                const linkedId = input.dataset.linkedId ? parseInt(input.dataset.linkedId) : null;
                val = { original: val, linked_id: linkedId };
            }

            newValue[partName] = val;
        });

        try {
            const response = await fetch(`/api/responses/${responseId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    field_id: fieldId,
                    new_value: newValue,
                    reason
                })
            });
            const data = await response.json();

            if (data.success) {
                document.getElementById('edit-composite-dialog').close();
                location.reload();
            } else {
                alert(data.error || 'Ошибка сохранения');
            }
        } catch (err) {
            alert('Сетевая ошибка: ' + err.message);
        }
    });
});