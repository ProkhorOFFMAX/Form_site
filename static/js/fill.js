document.querySelectorAll('.inst-type').forEach(function(typeSelect){
    typeSelect.addEventListener('change', function (){
        const type = this.value;
        const nameSelect = this.nextElementSibling;

        nameSelect.innerHTML = '<option value="">Загрузка...</option>';

        fetch(`/api/institutions/${encodeURIComponent(type)}`)
            .then(r => r.json())
            .then(data => {
                nameSelect.innerHTML = '<option value="">— выберите ОУ —</option>';
                data.forEach(item => {
                    const opt = document.createElement('option');
                    opt.value = item.id;
                    opt.textContent = item.short_name;
                    nameSelect.appendChild(opt);
                });
            })
            .catch(() => {
               nameSelect.innerHTML = '<option value="">Ошибка загрузки</option>'
            });
    });
});

document.querySelectorAll('.custom-select').forEach(async function(select) {
    const fieldId = select.dataset.fieldId;
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
        select.innerHTML = '<option value="">Ошибка загрузки</option>';
    }
});