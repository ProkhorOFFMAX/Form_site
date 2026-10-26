document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('table-body');
    const typeFilter = document.getElementById('type-filter');
    const btnDelete = document.getElementById('btn-delete');
    const btnEdit = document.getElementById('btn-edit');
    const btnCreate = document.getElementById('btn-create');
    const dialog = document.getElementById('edit-dialog');
    const dialogTitle = document.getElementById('dialog-title');
    const editForm = document.getElementById('edit-form');
    const editId = document.getElementById('edit-id');
    const editFull = document.getElementById('edit-full');
    const editShort = document.getElementById('edit-short');
    const editType = document.getElementById('edit-type');
    const dialogCancel = document.getElementById('dialog-cancel');

    let selectedRow = null;

    tableBody.addEventListener('click', function (e){
       const row = e.target.closest('tr');
       if (!row) return;

       tableBody.querySelectorAll('tr').forEach(r => r.classList.remove('selected'));

       row.classList.add('selected');
       selectedRow = row;

       btnDelete.disabled = false;
       btnEdit.disabled = false;
    });

    typeFilter.addEventListener("change", function() {
        const type = this.value;
        fetch(`/api/institutions/${encodeURIComponent(type)}`)
            .then(r => r.json())
            .then(data => {
                tableBody.innerHTML = '';
                data.forEach(inst => {
                    const tr = document.createElement('tr');
                    tr.dataset.id = inst.id;
                    tr.dataset.full = inst.full_name;
                    tr.dataset.short = inst.short_name;
                    tr.dataset.type = type;
                    tr.innerHTML = `<td>${inst.full_name}</td><td>${inst.short_name}</td><td></td>`;
                    tableBody.appendChild(tr);
                });
                selectedRow = null;
                btnDelete.disabled = true;
                btnEdit.disabled = true;
            });
    });

    btnDelete.addEventListener("click", function (){
        if (!selectedRow) return;
        const id = selectedRow.dataset.id;
        const name = selectedRow.dataset.short;

        if (!confirm(`Удалить ОУ «${name}»?`)) return;

        fetch(`/institutions/delete/${id}`, { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.success){
                    selectedRow.remove();
                    selectedRow = null;
                    btnDelete.disabled = true;
                    btnEdit.disabled = true;
                } else {
                    alert('Ошибка удаления: ' + (data.error || 'неизвестно'))
                }
            });
    });

    btnCreate.addEventListener('click', function (){
       dialogTitle.textContent = 'Создать ОУ';
       editFull.value = '';
       editShort.value = '';
       editType.value = typeFilter.value;
       dialog.showModal();
    });

    btnEdit.addEventListener('click', function (){
        if (!selectedRow) return;
        dialogTitle.textContent = 'Редактировать ОУ';
        editId.value = selectedRow.dataset.id;
        editFull.value = selectedRow.dataset.full;
        editShort.value = selectedRow.dataset.short;
        editType.value = selectedRow.dataset.type;
        dialog.showModal();
    });

    dialogCancel.addEventListener('click', function (){
       dialog.close();
    });

    editForm.addEventListener('submit', function (e) {
       e.preventDefault();
       const id = editId.value;
       const currentType = editType.value
       const payload = {
           full_name: editFull.value.trim(),
           short_name: editShort.value.trim(),
           type: editType.value
       };

       if (!payload.full_name || !payload.short_name) {
           alert('Заполните все поля');
           return;
       }
       const url = id ? `/institutions/edit/${id}` : '/institutions/create';
       const method = 'POST';

       const formData = new FormData()
       formData.append('full_name', payload.full_name);
       formData.append('short_name', payload.short_name);
       formData.append('type', payload.type);
       formData.append('current_type', currentType); // передаём фильтр

       fetch(url, { method: 'POST', body: formData })
           .then(r => {
               if (r.ok) {
                   dialog.close();
                   // Перезагружаем таблицу (простой способ)
                   window.location.href = `/institutions?type=${encodeURIComponent(currentType)}`;
               } else {
                   return r.json().then(err => {throw new Error(err.error || 'Ошибка'); });
               }
           });

    });
});