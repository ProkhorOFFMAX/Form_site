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